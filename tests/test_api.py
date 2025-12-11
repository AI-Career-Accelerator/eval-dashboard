"""
API test script - demonstrates all endpoints.
Make sure the API server is running first: python start_api.py
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"


def print_section(title):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def test_health():
    """Test health check endpoint."""
    print_section("1. Testing Health Check (GET /health)")

    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")

    return response.status_code == 200


def test_stats():
    """Test dashboard stats endpoint."""
    print_section("2. Testing Dashboard Stats (GET /stats)")

    response = requests.get(f"{BASE_URL}/stats")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")

    return response.status_code == 200


def test_models():
    """Test models endpoint."""
    print_section("3. Testing Models List (GET /models)")

    response = requests.get(f"{BASE_URL}/models")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Total models: {len(data['models'])}")
        print("\nModel Stats (top 5):")
        for i, model in enumerate(data['models'][:5], 1):
            print(f"  {i}. {model['model_name']}")
            print(f"     - Avg Accuracy: {model['avg_accuracy']:.2%}")
            print(f"     - Total Runs: {model['total_runs']}")
            print(f"     - Avg Cost: ${model['avg_cost']:.4f}")

    return response.status_code == 200


def test_runs():
    """Test runs list endpoint."""
    print_section("4. Testing Runs List (GET /runs)")

    # Test basic listing
    response = requests.get(f"{BASE_URL}/runs?page=1&page_size=5")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Total runs: {data['total']}")
        print(f"Page: {data['page']}, Page size: {data['page_size']}")
        print(f"Runs on this page: {len(data['runs'])}")

        if data['runs']:
            print("\nRecent runs:")
            for run in data['runs']:
                print(f"  - Run #{run['id']}: {run['model_name']} - {run['accuracy']:.2%} accuracy")

    return response.status_code == 200


def test_run_detail():
    """Test run detail endpoint."""
    print_section("5. Testing Run Detail (GET /run/{id})")

    # First get a run ID
    runs_response = requests.get(f"{BASE_URL}/runs?page=1&page_size=1")

    if runs_response.status_code == 200:
        data = runs_response.json()
        if data['runs']:
            run_id = data['runs'][0]['id']
            print(f"Testing with run ID: {run_id}\n")

            response = requests.get(f"{BASE_URL}/run/{run_id}")
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                detail = response.json()
                print(f"Model: {detail['run']['model_name']}")
                print(f"Accuracy: {detail['run']['accuracy']:.2%}")
                print(f"Total Questions: {detail['run']['total_questions']}")
                print(f"Evaluation Time: {detail['run']['evaluation_time']:.2f}s")
                print("\nCategory Breakdown:")
                for category, stats in detail['category_breakdown'].items():
                    print(f"  - {category}: {stats['avg_score']:.2%} ({stats['total_questions']} questions)")

                return True
        else:
            print("No runs available to test detail endpoint")
            return True

    return False


def test_drift():
    """Test drift analysis endpoint."""
    print_section("6. Testing Drift Analysis (GET /drift/{model})")

    # Test with a model that likely has runs
    model_name = "gpt-4o"
    response = requests.get(f"{BASE_URL}/drift/{model_name}?threshold=0.05")

    print(f"Testing drift for: {model_name}")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Has Drifted: {data['has_drifted']}")
        print(f"Accuracy Drop: {data['accuracy_drop']:.2%}")
        print(f"Threshold: {data['threshold']:.2%}")

        if data['latest_run']:
            print(f"\nLatest Run:")
            print(f"  - Accuracy: {data['latest_run']['accuracy']:.2%}")
            print(f"  - Timestamp: {data['latest_run']['timestamp']}")

        if data['best_run']:
            print(f"\nBest Run:")
            print(f"  - Accuracy: {data['best_run']['accuracy']:.2%}")
            print(f"  - Timestamp: {data['best_run']['timestamp']}")

        return True
    elif response.status_code == 404:
        print(f"Model '{model_name}' has no evaluation runs yet (expected if database is empty)")
        return True

    return False


def test_run_evaluation():
    """Test triggering a new evaluation (background task)."""
    print_section("7. Testing Run Evaluation (POST /run-evaluation)")

    print("⚠️  This will trigger a background evaluation!")
    print("Enter 'yes' to proceed, or anything else to skip:")

    user_input = input("> ").strip().lower()

    if user_input != 'yes':
        print("Skipping evaluation test...")
        return True

    # Trigger evaluation with just one model and limited questions for quick test
    payload = {
        "models": ["gpt-4o-mini"],
        "max_questions": 5,
        "webhook_url": None  # Set to your webhook URL if you want to test callbacks
    }

    print(f"\nTriggering evaluation with payload:")
    print(json.dumps(payload, indent=2))

    response = requests.post(f"{BASE_URL}/run-evaluation", json=payload)
    print(f"\nStatus Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        print(f"\n✅ Evaluation started! Job ID: {data['job_id']}")
        print("Check your console where the API server is running to see progress.")
        print("Results will be saved to the database when complete.")

        return True

    return False


def main():
    """Run all API tests."""
    print("=" * 80)
    print("  🧪 Eval Dashboard API Test Suite")
    print("=" * 80)
    print("\nMake sure:")
    print("  1. The API server is running (python start_api.py)")
    print("  2. LiteLLM proxy is running (if testing evaluations)")
    print("  3. Database has been initialized")

    input("\nPress Enter to start tests...")

    tests = [
        ("Health Check", test_health),
        ("Dashboard Stats", test_stats),
        ("Models List", test_models),
        ("Runs List", test_runs),
        ("Run Detail", test_run_detail),
        ("Drift Analysis", test_drift),
        ("Run Evaluation", test_run_evaluation),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Error in {test_name}: {str(e)}")
            results.append((test_name, False))

        time.sleep(0.5)  # Small delay between tests

    # Print summary
    print_section("Test Results Summary")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")

    print(f"\n{'=' * 80}")
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
