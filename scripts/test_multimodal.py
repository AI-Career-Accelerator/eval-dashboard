"""
Quick test script for multi-modal evaluation.
Tests 5 questions: 3 text-only + 2 vision questions.
"""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.evaluate import load_dataset, evaluate_question
from core.db import init_db

load_dotenv()

def test_multimodal():
    """Test multi-modal evaluation on a small subset."""
    print("\n" + "="*60)
    print("MULTI-MODAL EVALUATION TEST")
    print("="*60 + "\n")

    # Initialize database
    print("[INIT] Initializing database...")
    init_db()

    # Load dataset
    print("[LOAD] Loading dataset...")
    questions = load_dataset()
    print(f"[OK] Loaded {len(questions)} questions\n")

    # Select test questions: 3 text-only + 2 vision
    test_questions = [
        questions[0],   # Text: reasoning
        questions[10],  # Text: math
        questions[20],  # Text: coding
        questions[50],  # Vision: OCR - sample_text.jpg ("Main Street")
        questions[60],  # Vision: reasoning - count_objects.jpg ("7")
    ]

    # Test model (use gpt-4o-mini for quick/cheap test, or gpt-4o for vision)
    # NOTE: gpt-4o-mini might not support vision - use gpt-4o if available
    test_model = "gpt-4o-mini"  # Change to "gpt-4o" if you have vision support

    print(f"[TEST] Testing {test_model} on {len(test_questions)} questions:\n")

    for i, q in enumerate(test_questions, 1):
        print(f"\n--- Question {i}/{len(test_questions)} ---")
        print(f"Category: {q['category']}")
        print(f"Question: {q['input']}")
        print(f"Expected: {q['expected_output']}")

        if q.get('image_path'):
            print(f"Image: {q['image_path']}")
            # Check if image exists
            img_path = os.path.join("data", q['image_path'])
            if os.path.exists(img_path):
                print(f"[OK] Image found")
            else:
                print(f"[WARNING] Image not found at {img_path}")

        print(f"\n[EVAL] Evaluating...")

        try:
            result = evaluate_question(test_model, q)

            print(f"Response: {result['model_response']}")
            print(f"Score: {result['score']}")
            print(f"Reasoning: {result['reasoning']}")
            print(f"Latency: {result.get('latency', 'N/A')}s")

        except Exception as e:
            print(f"[ERROR] Evaluation failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")

    print("[NEXT STEPS]")
    print("1. If vision questions failed, make sure LiteLLM proxy is running")
    print("2. Check that the model supports vision (gpt-4o, claude-sonnet, etc.)")
    print("3. Run full evaluation: python core/evaluate.py")

if __name__ == "__main__":
    test_multimodal()
