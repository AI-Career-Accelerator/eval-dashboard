"""
Background task processing and webhook callback logic.
"""
import os
import sys
import time
import csv
import json
import requests
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv


load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.judge import score_answer
from core.db import save_run


# LiteLLM proxy configuration
# Note: LiteLLM proxy handles actual provider API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
# This is just a placeholder key for connecting to the local proxy
API_KEY = "sk-test"
URL = "http://127.0.0.1:4000/chat/completions"


def load_dataset(csv_path: str = "data/golden_dataset.csv", max_questions: Optional[int] = None) -> List[Dict]:
    """Load golden dataset from CSV."""
    questions = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append({
                "id": row["id"],
                "category": row["category"],
                "input": row["input"],
                "expected_output": row["expected_output"]
            })

    if max_questions:
        questions = questions[:max_questions]

    return questions


def evaluate_question(model_name: str, question: Dict) -> Dict:
    """
    Evaluate a single question using the specified model.
    Includes retry logic with exponential backoff for timeout/connection errors.
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question['input']}
        ],
        "max_tokens": 300
    }

    # Retry configuration
    TIMEOUT = 120  # Increased from 60s to 120s
    MAX_RETRIES = 2  # Will try up to 3 times total (1 initial + 2 retries)
    BACKOFF_DELAYS = [5, 10]  # Wait 5s after first failure, 10s after second

    last_error = None
    retry_count = 0

    for attempt in range(MAX_RETRIES + 1):
        start_time = time.time()
        try:
            r = requests.post(URL, headers=headers, json=data, timeout=TIMEOUT)
            latency = time.time() - start_time

            if r.status_code == 200:
                content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                score, reasoning = score_answer(question['expected_output'], content)

                # Add retry info to reasoning if retried
                if retry_count > 0:
                    reasoning = f"[Succeeded after {retry_count} retries] {reasoning}"

                return {
                    "id": question["id"],
                    "category": question["category"],
                    "input": question["input"],
                    "expected_output": question["expected_output"],
                    "model_response": content,
                    "score": score,
                    "reasoning": reasoning,
                    "latency": latency
                }
            else:
                # Non-200 status code - don't retry, return immediately
                content = ""
                score, reasoning = 0.0, f"HTTP {r.status_code}: {r.text[:200]}"
                return {
                    "id": question["id"],
                    "category": question["category"],
                    "input": question["input"],
                    "expected_output": question["expected_output"],
                    "model_response": content,
                    "score": score,
                    "reasoning": reasoning,
                    "latency": latency
                }

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            # Timeout or connection error - retry with backoff
            last_error = e
            retry_count += 1

            if attempt < MAX_RETRIES:
                delay = BACKOFF_DELAYS[attempt]
                print(f"[RETRY] {model_name} Q{question['id']} - Attempt {attempt + 1} failed ({type(e).__name__}), retrying in {delay}s...")
                time.sleep(delay)
                continue
            else:
                # Max retries reached
                print(f"[FAIL] {model_name} Q{question['id']} - Max retries reached after {retry_count} attempts")
                break

        except Exception as e:
            # Other exceptions - don't retry
            last_error = e
            print(f"[ERROR] {model_name} Q{question['id']} - Non-retryable error: {type(e).__name__}")
            break

    # If we get here, all retries failed
    return {
        "id": question["id"],
        "category": question["category"],
        "input": question["input"],
        "expected_output": question["expected_output"],
        "model_response": None,
        "score": 0.0,
        "reasoning": f"Failed after {retry_count} retries: {type(last_error).__name__}: {str(last_error)}",
        "latency": None
    }


def evaluate_model_parallel(model_name: str, questions: List[Dict], max_workers: int = 5) -> tuple:
    """Evaluate all questions for a single model in parallel."""
    print(f"[START] Evaluating {model_name} in parallel...")
    start_model_time = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(evaluate_question, model_name, q) for q in questions]
        for future in as_completed(futures):
            results.append(future.result())

    model_elapsed = time.time() - start_model_time
    print(f"[TIMER] {model_name} evaluation time: {model_elapsed:.2f}s")
    return results, model_elapsed


def send_webhook(webhook_url: str, payload: Dict[str, Any]) -> bool:
    """Send results to webhook URL."""
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code in [200, 201, 202, 204]:
            print(f"[WEBHOOK] Successfully sent to {webhook_url}")
            return True
        else:
            print(f"[WEBHOOK] Failed: HTTP {response.status_code} - {response.text[:200]}")
            return False
    except Exception as e:
        print(f"[WEBHOOK] Error sending to {webhook_url}: {str(e)}")
        return False


def run_evaluation_task(
    models: List[str],
    webhook_url: Optional[str] = None,
    max_questions: Optional[int] = None,
    job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run evaluation in background and optionally send results to webhook.

    Args:
        models: List of model names to evaluate
        webhook_url: Optional callback URL for results
        max_questions: Optional limit on number of questions
        job_id: Unique identifier for this job

    Returns:
        Dictionary with evaluation results and metadata
    """
    print(f"[JOB {job_id}] Starting evaluation for {len(models)} models...")

    questions = load_dataset(max_questions=max_questions)
    all_results = []
    total_start_time = time.time()

    # Evaluate models in parallel (3 models at a time)
    with ThreadPoolExecutor(max_workers=3) as model_executor:
        model_futures = {
            model_executor.submit(evaluate_model_parallel, model, questions, max_workers=5): model
            for model in models
        }

        for future in as_completed(model_futures):
            model_name = model_futures[future]
            try:
                model_results, model_time = future.result()
                all_results.append({
                    "model": model_name,
                    "evaluation_time": model_time,
                    "results": model_results
                })
                print(f"[JOB {job_id}] Completed {model_name} in {model_time:.2f}s")

                # Save to database
                try:
                    run_id = save_run(model_name, model_results, model_time)
                    print(f"[JOB {job_id}] Saved to database as run #{run_id}")
                except Exception as db_error:
                    print(f"[JOB {job_id}] Database save failed for {model_name}: {db_error}")

            except Exception as e:
                print(f"[JOB {job_id}] {model_name} failed: {str(e)}")
                all_results.append({
                    "model": model_name,
                    "evaluation_time": 0,
                    "error": str(e),
                    "results": []
                })

    total_elapsed = time.time() - total_start_time

    # Prepare response payload
    payload = {
        "job_id": job_id,
        "status": "completed",
        "total_evaluation_time": total_elapsed,
        "total_questions": len(questions),
        "models_evaluated": len(models),
        "models": all_results
    }

    # Send webhook if provided
    if webhook_url:
        send_webhook(webhook_url, payload)

    print(f"[JOB {job_id}] Evaluation finished in {total_elapsed:.2f}s")

    return payload
