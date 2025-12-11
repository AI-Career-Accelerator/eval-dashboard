"""
Quick test script to validate Day 3 database integration.
Runs a small evaluation on 1-2 models with a few questions.
"""
import os
import csv
import json
import time
import requests
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.db import init_db, save_run, get_recent_runs, get_run_by_id
from judge import score_answer

load_dotenv()

API_KEY = os.getenv("API_KEY", "sk-test")
URL = "http://127.0.0.1:4000/chat/completions"

# Test with just 1-2 models for speed
TEST_MODELS = [
    "gpt-4o-mini",
    # "claude-haiku-4-5",  # Uncomment to test second model
]

def load_test_dataset(limit=5):
    """Load just the first few questions for quick testing."""
    questions = []
    with open("golden_dataset.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= limit:
                break
            questions.append({
                "id": row["id"],
                "category": row["category"],
                "input": row["input"],
                "expected_output": row["expected_output"]
            })
    return questions

def evaluate_question(model_name, q):
    """Evaluate a single question."""
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

    start_time = time.time()
    try:
        r = requests.post(URL, headers=headers, json=data, timeout=60)
        latency = time.time() - start_time

        if r.status_code == 200:
            content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            score, reasoning = score_answer(q['expected_output'], content)
        else:
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
    except Exception as e:
        return {
            "id": q["id"],
            "category": q["category"],
            "input": q["input"],
            "expected_output": q["expected_output"],
            "model_response": None,
            "score": 0.0,
            "reasoning": f"Exception: {str(e)}",
            "latency": None
        }

def test_database_integration():
    """Test the complete database integration."""
    print("\n" + "="*80)
    print("DAY 3 DATABASE INTEGRATION TEST")
    print("="*80 + "\n")

    # Step 1: Initialize database
    print("[1/5] Initializing database...")
    init_db()
    print("[OK] Database initialized\n")

    # Step 2: Load test data
    print("[2/5] Loading test dataset (5 questions)...")
    questions = load_test_dataset(limit=5)
    print(f"[OK] Loaded {len(questions)} questions\n")

    # Step 3: Run evaluation
    print(f"[3/5] Running evaluation on {len(TEST_MODELS)} model(s)...")
    for model_name in TEST_MODELS:
        print(f"\n  Testing model: {model_name}")
        start_time = time.time()
        results = []

        for i, q in enumerate(questions, 1):
            print(f"    Question {i}/{len(questions)}...", end=" ")
            result = evaluate_question(model_name, q)
            results.append(result)
            print(f"Score: {result['score']:.2f}")

        eval_time = time.time() - start_time
        print(f"  [OK] Completed in {eval_time:.2f}s")

        # Step 4: Save to database
        print(f"\n[4/5] Saving results to database...")
        try:
            run_id = save_run(model_name, results, eval_time)
            print(f"[OK] Saved as run #{run_id}\n")
        except Exception as e:
            print(f"[ERROR] Failed to save: {e}\n")
            return False

    # Step 5: Verify data was saved
    print("[5/5] Verifying saved data...")
    recent_runs = get_recent_runs(limit=5)

    if not recent_runs:
        print("[ERROR] No runs found in database!")
        return False

    print(f"[OK] Found {len(recent_runs)} run(s) in database")
    print("\nRecent runs:")
    for run in recent_runs:
        print(f"  Run #{run.id}: {run.model_name} | Accuracy: {run.accuracy:.2%} | Questions: {run.total_questions}")

    # Show detailed results for the latest run
    latest_run_id = recent_runs[0].id
    latest_run = get_run_by_id(latest_run_id)

    print(f"\nDetailed results for Run #{latest_run.id}:")
    print(f"  Model:       {latest_run.model_name}")
    print(f"  Timestamp:   {latest_run.timestamp}")
    print(f"  Accuracy:    {latest_run.accuracy:.2%}")
    avg_lat_str = f"{latest_run.avg_latency:.2f}s" if latest_run.avg_latency > 0 else "N/A"
    print(f"  Avg Latency: {avg_lat_str}")
    print(f"  Total Cost:  ${latest_run.total_cost:.4f}")
    print(f"  Commit Hash: {latest_run.commit_hash[:7] if latest_run.commit_hash else 'N/A'}")
    print(f"  Questions:   {latest_run.total_questions}")

    # Show a sample evaluation
    if latest_run.evaluations:
        print(f"\n  Sample evaluation (Question 1):")
        eval_sample = latest_run.evaluations[0]
        print(f"    Question:  {eval_sample.question_text[:80]}...")
        print(f"    Expected:  {eval_sample.expected_output}")
        print(f"    Response:  {(eval_sample.model_response or 'N/A')[:80]}...")
        print(f"    Score:     {eval_sample.judge_score:.2f}")
        latency_str = f"{eval_sample.latency:.2f}s" if eval_sample.latency is not None else "timeout"
        print(f"    Latency:   {latency_str}")

    print("\n" + "="*80)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("="*80)
    print("\nNext steps:")
    print("  1. Run 'python query_db.py' to see all runs")
    print("  2. Run 'python query_db.py run <id>' for detailed results")
    print("  3. Run 'python evaluate.py' for full evaluation (all models)")
    print()

    return True

if __name__ == "__main__":
    success = test_database_integration()
    sys.exit(0 if success else 1)
