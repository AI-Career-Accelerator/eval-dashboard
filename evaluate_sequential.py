import csv
import json
import time
import requests
import os
from dotenv import load_dotenv
from judge import score_answer

load_dotenv()

API_KEY = os.getenv("API_KEY", "sk-test")
URL = "http://127.0.0.1:4000/chat/completions"

MODELS = [
    "gpt-5-chat", "gpt-4o", "gpt-4o-mini",
    "claude-opus-4-5", "claude-sonnet-4-5", "claude-haiku-4-5",
    "Kimi-K2-Thinking", "DeepSeek-V3.1", "grok-3",
    "Mistral-Large-3"
]

# Load dataset
with open("golden_dataset.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    questions = list(reader)

print("Loaded CSV headers:", reader.fieldnames)

results = []

for model_name in MODELS:
    print(f"\n🚀 Evaluating {model_name}...")
    model_results = []

    for q in questions:
        user_input = q['input']
        expected_output = q['expected_output']

        start_time = time.time()

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input}
            ],
            "max_tokens": 300
        }

        try:
            r = requests.post(URL, headers=headers, json=data, timeout=30)
            latency = time.time() - start_time

            if r.status_code == 200:
                content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                score, reasoning = score_answer(expected_output, content)
            else:
                content = ""
                score, reasoning = 0.0, f"HTTP {r.status_code}: {r.text[:200]}"

            model_results.append({
                "id": q["id"],
                "category": q["category"],
                "input": user_input,
                "expected_output": expected_output,
                "model_response": content,
                "score": score,
                "reasoning": reasoning,
                "latency": latency
            })

        except Exception as e:
            model_results.append({
                "id": q["id"],
                "category": q["category"],
                "input": user_input,
                "expected_output": expected_output,
                "model_response": None,
                "score": 0.0,
                "reasoning": f"Exception: {str(e)}",
                "latency": None
            })

        time.sleep(0.2)

    results.append({"model": model_name, "results": model_results})

# Save output
with open("evaluation_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n✅ Evaluation complete! Saved → evaluation_results.json")
