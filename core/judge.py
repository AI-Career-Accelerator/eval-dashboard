import json
import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# LiteLLM proxy handles actual provider API keys from .env
# OpenAI SDK configured to use LiteLLM proxy
judge_client = OpenAI(
    api_key="sk-test",  # placeholder for LiteLLM proxy
    base_url="http://127.0.0.1:4000"  # LiteLLM proxy endpoint
)

def score_answer(expected: str, response: str):
    """
    Uses GPT-4o-mini via LiteLLM proxy to score a model response.
    Returns (score: float, reasoning: str)
    Now uses OpenAI SDK for automatic Phoenix tracing.
    """

    prompt = f"""
You are an objective evaluator.
Rate the correctness of the following answer compared to the expected answer.

Return ONLY JSON:
{{ "score": 0.0 to 1.0, "reasoning": "..." }}

Expected answer: {expected}
Model answer: {response}
"""

    try:
        start_time = time.time()

        # Use OpenAI SDK - automatically traced by Phoenix
        completion = judge_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a strict evaluator."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            timeout=25
        )

        elapsed = time.time() - start_time
        content = completion.choices[0].message.content

        try:
            parsed = json.loads(content)
            return float(parsed.get("score", 0.0)), parsed.get("reasoning", "")
        except:
            return 0.0, f"Invalid JSON from judge: {content}"

    except Exception as e:
        return 0.0, f"Exception: {str(e)}"
