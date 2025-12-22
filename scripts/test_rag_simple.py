"""
Simple RAG test - validates retrieval without requiring API calls
"""

import sys
sys.path.insert(0, 'core')

from retrieval import RetrievalSystem
import csv
import ast


def test_rag_retrieval_only():
    """Test only the retrieval component of RAG"""
    print("\n" + "="*60)
    print("RAG RETRIEVAL QUALITY TEST")
    print("="*60)

    # Initialize retriever
    retriever = RetrievalSystem()

    # Load RAG dataset
    questions = []
    with open('data/golden_dataset_rag.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                relevant_ids = ast.literal_eval(row['relevant_chunk_ids'])
                # Ensure it's a list
                if isinstance(relevant_ids, int):
                    relevant_ids = [relevant_ids]
                elif not isinstance(relevant_ids, list):
                    relevant_ids = []
            except Exception as e:
                print(f"Warning: Failed to parse relevant_chunk_ids for Q{row['id']}: {e}")
                relevant_ids = []

            questions.append({
                'id': row['id'],
                'category': row['category'],
                'question': row['input'],
                'relevant_ids': relevant_ids
            })

    # Test on first 15 questions
    print(f"\nTesting retrieval on first 15 questions...\n")

    total_precision = 0
    total_recall = 0
    total_f1 = 0
    total_mrr = 0

    for i, q in enumerate(questions[:15], 1):
        # Retrieve
        metrics = retriever.evaluate_retrieval(
            q['question'],
            q['relevant_ids'],
            top_k=5
        )

        total_precision += metrics['precision_at_k']
        total_recall += metrics['recall_at_k']
        total_f1 += metrics['f1_at_k']
        total_mrr += metrics['mrr']

        # Show results
        print(f"[{i}] Q{q['id']}: {q['category']}")
        print(f"    Question: {q['question'][:70]}...")
        print(f"    Ground Truth: {q['relevant_ids']}")
        print(f"    Retrieved: {metrics['retrieved_chunk_ids']}")
        print(f"    Metrics: P={metrics['precision_at_k']:.2f} "
              f"R={metrics['recall_at_k']:.2f} "
              f"F1={metrics['f1_at_k']:.2f} "
              f"MRR={metrics['mrr']:.2f}")

        if metrics['f1_at_k'] < 0.5:
            print(f"    [WARNING] Low F1 score!")
        print()

    # Summary
    n = 15
    print("=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    print(f"Avg Precision@5: {total_precision/n:.2%}")
    print(f"Avg Recall@5:    {total_recall/n:.2%}")
    print(f"Avg F1@5:        {total_f1/n:.2%}")
    print(f"Avg MRR:         {total_mrr/n:.3f}")
    print("=" * 60)

    # Pass/fail
    if total_precision/n > 0.4 and total_recall/n > 0.5:
        print("\n[OK] Retrieval system performing well!")
        print("You can now run the full RAG evaluation with generation.")
    else:
        print("\n[WARNING] Retrieval performance below threshold.")
        print("Consider adjusting top_k or embedding model.")


if __name__ == "__main__":
    test_rag_retrieval_only()
