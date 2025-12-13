import os
import csv
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from core.judge import score_answer  # <-- use your real judge
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import init_db, save_run

load_dotenv()

# LiteLLM proxy handles actual provider API keys from .env
# This is just a placeholder for connecting to the local proxy
API_KEY = "sk-test"
URL = "http://127.0.0.1:4000/chat/completions"

# List of models
MODELS = [
    "gpt-5-chat",
    "gpt-4o",
    "gpt-4o-mini",
    "claude-opus-4-5",
    "claude-sonnet-4-5",
    "claude-haiku-4-5",
    "Kimi-K2-Thinking",
    "DeepSeek-V3.1",
    "grok-3",
    "Mistral-Large-3",
    "Llama-4-Maverick-17B-128E-Instruct-FP8"
]

# Load golden dataset CSV
def load_dataset(csv_path="data/golden_dataset.csv"):
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
    return questions

# Evaluate a single question using the judge
def evaluate_question(model_name, q):
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
            {"role": "user", "content": q['input']}
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
                # Use the judge module for scoring
                score, reasoning = score_answer(q['expected_output'], content)

                # Add retry info to reasoning if retried
                if retry_count > 0:
                    reasoning = f"[Succeeded after {retry_count} retries] {reasoning}"

                return {
                    "id": q["id"],
                    "category": q["category"],
                    "input": q["input"],
                    "expected_output": q["expected_output"],
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
                    "id": q["id"],
                    "category": q["category"],
                    "input": q["input"],
                    "expected_output": q["expected_output"],
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
                print(f"[RETRY] {model_name} Q{q['id']} - Attempt {attempt + 1} failed ({type(e).__name__}), retrying in {delay}s...")
                time.sleep(delay)
                continue
            else:
                # Max retries reached
                print(f"[FAIL] {model_name} Q{q['id']} - Max retries reached after {retry_count} attempts")
                break

        except Exception as e:
            # Other exceptions - don't retry
            last_error = e
            print(f"[ERROR] {model_name} Q{q['id']} - Non-retryable error: {type(e).__name__}")
            break

    # If we get here, all retries failed
    return {
        "id": q["id"],
        "category": q["category"],
        "input": q["input"],
        "expected_output": q["expected_output"],
        "model_response": None,
        "score": 0.0,
        "reasoning": f"Failed after {retry_count} retries: {type(last_error).__name__}: {str(last_error)}",
        "latency": None
    }

# Evaluate all questions for a single model in parallel
def evaluate_model_parallel(model_name, questions, max_workers=5):
    print(f"\n[START] Evaluating {model_name} in parallel...")
    start_model_time = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(evaluate_question, model_name, q) for q in questions]
        for future in as_completed(futures):
            results.append(future.result())
    model_elapsed = time.time() - start_model_time
    print(f"[TIMER] {model_name} evaluation time: {model_elapsed:.2f}s")
    return results, model_elapsed

# Main evaluation
def main():
    # Initialize database
    print("[INIT] Initializing database...")
    init_db()

    questions = load_dataset()
    all_results = []
    total_start_time = time.time()

    # Parallel model evaluation
    with ThreadPoolExecutor(max_workers=3) as model_executor:
        model_futures = {
            model_executor.submit(evaluate_model_parallel, model, questions, max_workers=5): model
            for model in MODELS
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
                print(f"[OK] Completed {model_name} in {model_time:.2f}s")

                # Save to database
                try:
                    run_id = save_run(model_name, model_results, model_time)
                    print(f"[DB] Saved to database as run #{run_id}")
                except Exception as db_error:
                    print(f"[WARNING] Database save failed for {model_name}: {db_error}")

            except Exception as e:
                print(f"[ERROR] {model_name} failed: {str(e)}")

    total_elapsed = time.time() - total_start_time

    # Save results to JSON (backup)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = f"evaluation_results_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_evaluation_time": total_elapsed,
            "models": all_results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n[DONE] Evaluation finished in {total_elapsed:.2f}s.")
    print(f"[JSON] Backup saved to {output_file}")
    print(f"[DB] Database updated: eval_dashboard.db")

if __name__ == "__main__":
    main()
