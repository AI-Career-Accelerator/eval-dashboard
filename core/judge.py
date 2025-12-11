import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

# LiteLLM proxy handles actual provider API keys from .env
# This is just a placeholder for connecting to the local proxy
URL = "http://127.0.0.1:4000/chat/completions"
API_KEY = "sk-test"

def score_answer(expected: str, response: str):
    """
    Uses GPT-4o-mini via LiteLLM proxy to score a model response.
    Returns (score: float, reasoning: str)
    """

    prompt = f"""
You are an objective evaluator.
Rate the correctness of the following answer compared to the expected answer.

Return ONLY JSON:
{{ "score": 0.0 to 1.0, "reasoning": "..." }}

Expected answer: {expected}
Model answer: {response}
"""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a strict evaluator."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 200
    }

    try:
        start_time = time.time()
        r = requests.post(URL, headers=headers, json=data, timeout=25)
        elapsed = time.time() - start_time

        if r.status_code != 200:
            return 0.0, f"HTTP {r.status_code}: {r.text[:200]}"

        content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")

        try:
            parsed = json.loads(content)
            return float(parsed.get("score", 0.0)), parsed.get("reasoning", "")
        except:
            return 0.0, f"Invalid JSON from judge: {content}"

    except Exception as e:
        return 0.0, f"Exception: {str(e)}"
