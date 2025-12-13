"""
Trigger a full evaluation run on all models and all questions.
"""
import requests
import time
import sys

API_URL = "http://127.0.0.1:8000"

def trigger_evaluation():
    """Trigger full evaluation via API."""
    print("🚀 Triggering full evaluation...")
    print("📊 All 11 models × 56 questions = 616 evaluations")
    print("⏱️  Estimated time: ~10-15 minutes\n")

    try:
        response = requests.post(
            f"{API_URL}/run-evaluation",
            json={},  # Empty = all models, all questions
            timeout=5
        )
        response.raise_for_status()
        data = response.json()

        print(f"✅ Evaluation started!")
        print(f"📋 Job ID: {data['job_id']}")
        print(f"🤖 Models: {len(data['models'])} models")
        print(f"\nModels being evaluated:")
        for i, model in enumerate(data['models'], 1):
            print(f"  {i}. {model}")

        print("\n" + "="*60)
        print("💡 Monitor progress:")
        print(f"   - Check API logs in the terminal where it's running")
        print(f"   - Refresh dashboard to see new runs appear")
        print(f"   - Check database: python scripts/query_db.py")
        print("="*60)

        return True

    except requests.exceptions.ConnectionError:
        print("❌ Error: FastAPI server not running")
        print("   Start it with: python scripts/start_api.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_recent_runs():
    """Check recent evaluation runs."""
    print("\n📊 Checking recent runs...\n")
    try:
        response = requests.get(f"{API_URL}/runs?page_size=10", timeout=5)
        response.raise_for_status()
        data = response.json()

        runs = data.get('runs', [])
        if not runs:
            print("No runs found yet.")
            return

        print(f"Total runs in database: {data.get('total', 0)}\n")
        print("Recent runs:")
        print("-" * 80)
        for run in runs[:5]:
            print(f"{run['model_name']:30} | Accuracy: {run['accuracy']:.1%} | {run['timestamp'][:19]}")
        print("-" * 80)

    except Exception as e:
        print(f"Could not fetch runs: {e}")


if __name__ == "__main__":
    # Check if API is running
    try:
        health = requests.get(f"{API_URL}/health", timeout=15)
        if health.status_code not in [200, 503]:  # 503 = degraded but still working
            print("⚠️  API returned unexpected status")
    except requests.exceptions.ConnectionError:
        print("❌ FastAPI server is not running on port 8000!")
        print("   Start it first: python scripts/start_api.py")
        sys.exit(1)
    except Exception as e:
        print(f"⚠️  Could not verify API status: {e}")
        print("   Continuing anyway...")

    # Trigger evaluation
    success = trigger_evaluation()

    if success:
        print("\n⏳ Waiting for first results (30 seconds)...")
        time.sleep(30)
        check_recent_runs()

        print("\n💡 Tip: Refresh your dashboard to see new runs!")
        print("   Dashboard: http://localhost:8501")
