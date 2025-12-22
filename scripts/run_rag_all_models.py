"""
Run RAG evaluation on all available models
Evaluates retrieval quality, answer correctness, and grounding for each model
"""

import sys
import os
sys.path.insert(0, 'core')

from rag_evaluate import RAGEvaluator

# Models to evaluate (from your existing setup)
MODELS_TO_EVALUATE = [
    "gpt-5-chat",
    "gpt-4o",
    "gpt-4o-mini",
    "claude-opus-4-5",
    "claude-sonnet-4-5",
    "claude-haiku-4-5",
    "DeepSeek-V3.1",
    "grok-3",
    # Add more models as needed
]

def main():
    print("\n" + "="*70)
    print("RAG EVALUATION - ALL MODELS")
    print("="*70)
    print(f"Models to evaluate: {len(MODELS_TO_EVALUATE)}")
    print(f"Questions per model: 50 (full RAG dataset)")
    print(f"Retrieval: Top-5 chunks per question")
    print("="*70 + "\n")

    for i, model in enumerate(MODELS_TO_EVALUATE, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(MODELS_TO_EVALUATE)}] Evaluating: {model}")
        print(f"{'='*70}\n")

        try:
            evaluator = RAGEvaluator(
                dataset_path="data/golden_dataset_rag.csv",
                retrieval_k=5,
                model=model
            )

            # Run evaluation on all 50 questions
            # Use sequential processing for stability
            summary = evaluator.evaluate_all(
                parallel=False,  # Sequential for reliability
                max_workers=3,
                save_to_db=True
            )

            print(f"\n[OK] {model} completed successfully!")
            print(f"  Recall: {summary['retrieval_metrics']['avg_recall_at_k']:.1%}")
            print(f"  Answer Score: {summary['answer_metrics']['avg_answer_score']:.1%}")
            print(f"  Grounding: {summary['answer_metrics']['avg_grounding_score']:.1%}")

        except Exception as e:
            print(f"\n[ERROR] {model} failed: {str(e)}")
            print(f"[INFO] Continuing with next model...\n")
            continue

    print("\n" + "="*70)
    print("RAG EVALUATION COMPLETE!")
    print("="*70)
    print("\nView results in the dashboard:")
    print("  1. Navigate to http://localhost:8501")
    print("  2. Click 'RAG Analysis' in the sidebar")
    print("  3. Select models to compare")
    print("\nOr query via API:")
    print("  curl http://127.0.0.1:8000/rag-runs")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
