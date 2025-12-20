import os
import sys
import csv
import json
import time
import warnings
import base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from openai import OpenAI

# Suppress Windows cleanup warnings (harmless Phoenix temp file cleanup)
warnings.filterwarnings('ignore', category=ResourceWarning)

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.judge import score_answer
from core.db import init_db, save_run
from core.phoenix_config import initialize_phoenix

load_dotenv()

# Initialize Phoenix for tracing (auto-instruments OpenAI calls)
# Set DISABLE_PHOENIX=1 in environment to skip Phoenix initialization
ENABLE_PHOENIX = os.getenv("DISABLE_PHOENIX") != "1"

if ENABLE_PHOENIX:
    print("\n[Phoenix] Initializing observability...")
    phoenix_session = initialize_phoenix(launch_server=True, enable_tracing=True)
else:
    print("\n[Phoenix] Disabled (set DISABLE_PHOENIX=1)")
    phoenix_session = None

# LiteLLM proxy handles actual provider API keys from .env
# OpenAI SDK configured to use LiteLLM proxy
client = OpenAI(
    api_key="sk-test",  # placeholder for LiteLLM proxy
    base_url="http://127.0.0.1:4000"  # LiteLLM proxy endpoint
)

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
            # Handle image_path field (may be None or empty string)
            image_path = row.get("image_path") or ""
            image_path = image_path.strip() if image_path else None

            questions.append({
                "id": row["id"],
                "category": row["category"],
                "input": row["input"],
                "expected_output": row["expected_output"],
                "image_path": image_path
            })
    return questions

# Helper function to encode images as base64
def encode_image_to_base64(image_path):
    """
    Encode an image file to base64 string.
    Returns None if file doesn't exist or can't be read.
    """
    try:
        # Handle relative paths from data directory
        if not os.path.isabs(image_path):
            image_path = os.path.join("data", image_path)

        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')

            # Detect image type from extension
            ext = Path(image_path).suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            mime_type = mime_types.get(ext, 'image/jpeg')

            return f"data:{mime_type};base64,{encoded}"
    except Exception as e:
        print(f"[WARNING] Failed to encode image {image_path}: {e}")
        return None

# Evaluate a single question using the judge
def evaluate_question(model_name, q):
    """
    Evaluate a single question using the specified model.
    Includes retry logic with exponential backoff for timeout/connection errors.
    Now uses OpenAI SDK for automatic Phoenix tracing.
    Supports multi-modal (vision) questions with images.
    """
    # Retry configuration
    TIMEOUT = 120  # Timeout for API calls
    MAX_RETRIES = 2  # Will try up to 3 times total (1 initial + 2 retries)
    BACKOFF_DELAYS = [5, 10]  # Wait 5s after first failure, 10s after second

    last_error = None
    retry_count = 0

    # Check if this is a vision question
    has_image = q.get('image_path') is not None
    image_base64 = None

    if has_image:
        image_base64 = encode_image_to_base64(q['image_path'])
        if not image_base64:
            # Image encoding failed - skip this question
            return {
                "id": q["id"],
                "category": q["category"],
                "input": q["input"],
                "expected_output": q["expected_output"],
                "model_response": None,
                "score": 0.0,
                "reasoning": f"Image file not found or unreadable: {q['image_path']}",
                "latency": None,
                "image_path": q['image_path']
            }

    for attempt in range(MAX_RETRIES + 1):
        start_time = time.time()
        try:
            # Build message content based on whether we have an image
            if has_image and image_base64:
                user_message = {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": q['input']
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_base64
                            }
                        }
                    ]
                }
            else:
                user_message = {
                    "role": "user",
                    "content": q['input']
                }

            # Use OpenAI SDK - automatically traced by Phoenix
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    user_message
                ],
                max_tokens=300,
                timeout=TIMEOUT
            )
            latency = time.time() - start_time

            content = response.choices[0].message.content

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
                "latency": latency,
                "image_path": q.get('image_path')
            }

        except Exception as e:
            # Handle timeout and connection errors with retry
            error_type = type(e).__name__
            last_error = e

            # Determine if we should retry
            should_retry = "timeout" in str(e).lower() or "connection" in str(e).lower()

            if should_retry and attempt < MAX_RETRIES:
                retry_count += 1
                delay = BACKOFF_DELAYS[attempt]
                print(f"[RETRY] {model_name} Q{q['id']} - Attempt {attempt + 1} failed ({error_type}), retrying in {delay}s...")
                time.sleep(delay)
                continue
            else:
                # Max retries reached or non-retryable error
                if retry_count > 0:
                    print(f"[FAIL] {model_name} Q{q['id']} - Max retries reached after {retry_count} attempts")
                else:
                    print(f"[ERROR] {model_name} Q{q['id']} - Non-retryable error: {error_type}")
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
        "latency": None,
        "image_path": q.get('image_path')
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
