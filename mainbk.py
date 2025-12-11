import os
import requests
from dotenv import load_dotenv
from typing import Dict, List
import time

load_dotenv()

# Configuration
API_KEY = "sk-test"
URL = "http://127.0.0.1:4000/chat/completions"

# All models from your config
MODELS = [
    "gpt-5-chat",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
    "o1",
    "claude-sonnet-4.5",
    "claude-haiku-4.5",
    "claude-opus-4.1",
    "deepseek-v3",
    "deepseek-coder"
]

def test_model(model_name: str) -> Dict:
    """Test a single model and return results"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello! I am working correctly.' and tell me your model name."}
        ],
        "max_tokens": 100
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(URL, headers=headers, json=data, timeout=30)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "No response")
            return {
                "status": "✅ SUCCESS",
                "model": model_name,
                "response": content[:150],  # First 150 chars
                "time": f"{elapsed_time:.2f}s",
                "error": None
            }
        else:
            return {
                "status": "❌ FAILED",
                "model": model_name,
                "response": None,
                "time": f"{elapsed_time:.2f}s",
                "error": f"HTTP {response.status_code}: {response.text[:200]}"
            }
    except requests.exceptions.Timeout:
        return {
            "status": "⏱️ TIMEOUT",
            "model": model_name,
            "response": None,
            "time": "30s+",
            "error": "Request timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "status": "❌ ERROR",
            "model": model_name,
            "response": None,
            "time": f"{time.time() - start_time:.2f}s",
            "error": str(e)
        }

def print_result(result: Dict):
    """Pretty print a single test result"""
    print(f"\n{'='*80}")
    print(f"Model: {result['model']}")
    print(f"Status: {result['status']}")
    print(f"Time: {result['time']}")
    
    if result['response']:
        print(f"Response: {result['response']}")
    
    if result['error']:
        print(f"Error: {result['error']}")
    print(f"{'='*80}")

def test_all_models():
    """Test all models and generate a summary report"""
    print("🚀 Starting model testing...\n")
    
    results = []
    
    for model in MODELS:
        print(f"Testing {model}...", end=" ")
        result = test_model(model)
        results.append(result)
        print(result['status'])
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    # Print detailed results
    print("\n" + "="*80)
    print("DETAILED RESULTS")
    print("="*80)
    
    for result in results:
        print_result(result)
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    success = sum(1 for r in results if r['status'] == "✅ SUCCESS")
    failed = sum(1 for r in results if r['status'] in ["❌ FAILED", "❌ ERROR"])
    timeout = sum(1 for r in results if r['status'] == "⏱️ TIMEOUT")
    
    print(f"\nTotal models tested: {len(results)}")
    print(f"✅ Successful: {success}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️ Timeout: {timeout}")
    print(f"\nSuccess rate: {(success/len(results)*100):.1f}%")
    
    # List failed models
    if failed + timeout > 0:
        print("\n⚠️ Models that need attention:")
        for result in results:
            if result['status'] != "✅ SUCCESS":
                print(f"  - {result['model']}: {result['error']}")

def test_specific_models(model_list: List[str]):
    """Test specific models from a list"""
    print(f"🚀 Testing {len(model_list)} specific models...\n")
    
    for model in model_list:
        if model in MODELS:
            result = test_model(model)
            print_result(result)
        else:
            print(f"⚠️ Model '{model}' not found in configuration")

if __name__ == "__main__":
    # Test all models
    test_all_models()
    
    # Or test specific models:
    # test_specific_models(["gpt-4o", "claude-sonnet-4.5", "gemini-pro-1.5"])