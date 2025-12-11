"""
Simple script to query the eval dashboard database.
Useful for inspecting stored evaluation runs and results.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.db import get_recent_runs, get_runs_by_model, get_run_by_id, get_drift_analysis, init_db


def print_recent_runs(limit=10):
    """Print the most recent evaluation runs."""
    print(f"\n{'='*80}")
    print(f"RECENT EVALUATION RUNS (last {limit})")
    print(f"{'='*80}\n")

    runs = get_recent_runs(limit)

    if not runs:
        print("No runs found in database.")
        return

    for run in runs:
        print(f"Run #{run.id} | {run.model_name}")
        print(f"  Timestamp:  {run.timestamp}")
        print(f"  Accuracy:   {run.accuracy:.2%} ({run.total_questions} questions)")
        print(f"  Latency:    {run.avg_latency:.2f}s avg")
        print(f"  Cost:       ${run.total_cost:.4f}")
        print(f"  Commit:     {run.commit_hash[:7] if run.commit_hash else 'N/A'}")
        print()


def print_run_details(run_id):
    """Print detailed results for a specific run."""
    print(f"\n{'='*80}")
    print(f"DETAILED RESULTS FOR RUN #{run_id}")
    print(f"{'='*80}\n")

    run = get_run_by_id(run_id)

    if not run:
        print(f"Run #{run_id} not found.")
        return

    print(f"Model:      {run.model_name}")
    print(f"Timestamp:  {run.timestamp}")
    print(f"Accuracy:   {run.accuracy:.2%}")
    avg_lat_str = f"{run.avg_latency:.2f}s" if run.avg_latency > 0 else "N/A (timeouts)"
    print(f"Avg Latency: {avg_lat_str}")
    print(f"Total Cost: ${run.total_cost:.4f}")
    print(f"Questions:  {run.total_questions}")
    print(f"Eval Time:  {run.evaluation_time:.2f}s")
    print(f"Commit:     {run.commit_hash or 'N/A'}")

    print(f"\n{'='*80}")
    print(f"INDIVIDUAL QUESTION RESULTS")
    print(f"{'='*80}\n")

    for i, eval_record in enumerate(run.evaluations[:10], 1):  # Show first 10
        print(f"{i}. Question {eval_record.question_id} [{eval_record.category}]")
        print(f"   Question: {eval_record.question_text[:100]}...")
        print(f"   Expected: {eval_record.expected_output[:100]}")
        print(f"   Response: {(eval_record.model_response or 'N/A')[:100]}...")
        print(f"   Score:    {eval_record.judge_score:.2f}")
        latency_str = f"{eval_record.latency:.2f}s" if eval_record.latency is not None else "timeout"
        print(f"   Latency:  {latency_str}")
        print()

    if len(run.evaluations) > 10:
        print(f"... and {len(run.evaluations) - 10} more questions")


def print_model_history(model_name):
    """Print all runs for a specific model."""
    print(f"\n{'='*80}")
    print(f"EVALUATION HISTORY FOR: {model_name}")
    print(f"{'='*80}\n")

    runs = get_runs_by_model(model_name)

    if not runs:
        print(f"No runs found for {model_name}.")
        return

    print(f"Total runs: {len(runs)}\n")

    for run in runs:
        print(f"Run #{run.id} | {run.timestamp} | Accuracy: {run.accuracy:.2%} | Cost: ${run.total_cost:.4f}")


def print_drift_report(model_name):
    """Print drift analysis for a model."""
    print(f"\n{'='*80}")
    print(f"DRIFT ANALYSIS FOR: {model_name}")
    print(f"{'='*80}\n")

    latest, best, has_drifted = get_drift_analysis(model_name, threshold=0.05)

    if not latest:
        print(f"No runs found for {model_name}.")
        return

    print(f"Latest Run #{latest.id}:")
    print(f"  Timestamp: {latest.timestamp}")
    print(f"  Accuracy:  {latest.accuracy:.2%}")
    print()

    print(f"Best Run #{best.id}:")
    print(f"  Timestamp: {best.timestamp}")
    print(f"  Accuracy:  {best.accuracy:.2%}")
    print()

    accuracy_diff = latest.accuracy - best.accuracy
    print(f"Accuracy Delta: {accuracy_diff:+.2%}")

    if has_drifted:
        print(f"\n[WARNING] DRIFT DETECTED! Accuracy dropped by more than 5%")
        print(f"   Action required: Investigate model degradation")
    else:
        print(f"\n[OK] No significant drift detected")


if __name__ == "__main__":
    # Initialize DB
    init_db()

    # Default: show recent runs
    if len(sys.argv) == 1:
        print_recent_runs()
        print("\nUsage:")
        print("  python query_db.py               - Show recent runs")
        print("  python query_db.py run <id>      - Show detailed results for a run")
        print("  python query_db.py model <name>  - Show history for a model")
        print("  python query_db.py drift <name>  - Show drift analysis for a model")

    elif len(sys.argv) >= 2:
        command = sys.argv[1].lower()

        if command == "run" and len(sys.argv) >= 3:
            run_id = int(sys.argv[2])
            print_run_details(run_id)

        elif command == "model" and len(sys.argv) >= 3:
            model_name = sys.argv[2]
            print_model_history(model_name)

        elif command == "drift" and len(sys.argv) >= 3:
            model_name = sys.argv[2]
            print_drift_report(model_name)

        else:
            print("Invalid command. Use: run <id>, model <name>, or drift <name>")
