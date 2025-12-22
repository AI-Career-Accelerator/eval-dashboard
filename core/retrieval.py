"""
RAG Retrieval System
Implements semantic search over knowledge base using sentence transformers
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle


class RetrievalSystem:
    """Vector-based retrieval system for RAG evaluation"""

    def __init__(
        self,
        knowledge_base_path: str = "data/knowledge_base.json",
        model_name: str = "all-MiniLM-L6-v2",
        cache_dir: str = "data/embeddings"
    ):
        """
        Initialize retrieval system

        Args:
            knowledge_base_path: Path to knowledge base JSON
            model_name: HuggingFace sentence transformer model
            cache_dir: Directory to cache embeddings
        """
        self.knowledge_base_path = knowledge_base_path
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load knowledge base
        self.documents = self._load_knowledge_base()

        # Initialize embedding model
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)

        # Load or create embeddings
        self.embeddings = self._load_or_create_embeddings()

        print(f"[OK] Retrieval system initialized with {len(self.documents)} documents")

    def _load_knowledge_base(self) -> List[Dict]:
        """Load knowledge base from JSON"""
        with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['documents']

    def _get_cache_path(self) -> Path:
        """Get path to cached embeddings"""
        # Include model name in cache filename
        safe_model_name = self.model_name.replace('/', '_')
        return self.cache_dir / f"embeddings_{safe_model_name}.pkl"

    def _load_or_create_embeddings(self) -> np.ndarray:
        """Load embeddings from cache or create new ones"""
        cache_path = self._get_cache_path()

        # Try loading from cache
        if cache_path.exists():
            print(f"Loading cached embeddings from {cache_path}")
            with open(cache_path, 'rb') as f:
                cached_data = pickle.load(f)

            # Verify cache is valid
            if len(cached_data) == len(self.documents):
                return cached_data
            else:
                print(f"[WARNING] Cache size mismatch. Regenerating embeddings...")

        # Create new embeddings
        print(f"Creating embeddings for {len(self.documents)} documents...")
        texts = [doc['content'] for doc in self.documents]
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        # Cache for future use
        with open(cache_path, 'wb') as f:
            pickle.dump(embeddings, f)
        print(f"[OK] Embeddings cached to {cache_path}")

        return embeddings

    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Retrieve top-k most relevant documents for a query

        Args:
            query: Search query
            top_k: Number of documents to retrieve

        Returns:
            List of dicts with keys: chunk_id, content, domain, topic, score
        """
        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]

        # Compute cosine similarity
        similarities = self._cosine_similarity(query_embedding, self.embeddings)

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        # Build results
        results = []
        for idx in top_indices:
            doc = self.documents[idx].copy()
            doc['score'] = float(similarities[idx])
            doc['rank'] = len(results) + 1
            results.append(doc)

        return results

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> np.ndarray:
        """Compute cosine similarity between vector and matrix"""
        # Normalize vectors
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-10)
        vec2_norm = vec2 / (np.linalg.norm(vec2, axis=1, keepdims=True) + 1e-10)

        # Compute dot product
        return np.dot(vec2_norm, vec1_norm)

    def get_document_by_id(self, chunk_id: int) -> Dict:
        """Get document by chunk_id"""
        for doc in self.documents:
            if doc['chunk_id'] == chunk_id:
                return doc
        raise ValueError(f"Document with chunk_id {chunk_id} not found")

    def evaluate_retrieval(
        self,
        query: str,
        relevant_chunk_ids: List[int],
        top_k: int = 5
    ) -> Dict[str, float]:
        """
        Evaluate retrieval quality for a single query

        Args:
            query: Search query
            relevant_chunk_ids: Ground truth relevant chunk IDs
            top_k: Number of documents to retrieve

        Returns:
            Dict with precision@k, recall@k, f1@k, mrr, avg_score
        """
        # Retrieve documents
        results = self.retrieve(query, top_k=top_k)
        retrieved_ids = [doc['chunk_id'] for doc in results]

        # Convert to sets for evaluation
        relevant_set = set(relevant_chunk_ids)
        retrieved_set = set(retrieved_ids)

        # True positives
        tp = len(relevant_set & retrieved_set)

        # Precision@K
        precision = tp / top_k if top_k > 0 else 0.0

        # Recall@K
        recall = tp / len(relevant_set) if len(relevant_set) > 0 else 0.0

        # F1@K
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # Mean Reciprocal Rank (MRR)
        mrr = 0.0
        for rank, chunk_id in enumerate(retrieved_ids, start=1):
            if chunk_id in relevant_set:
                mrr = 1.0 / rank
                break

        # Average relevance score
        avg_score = np.mean([doc['score'] for doc in results]) if results else 0.0

        return {
            'precision_at_k': round(precision, 4),
            'recall_at_k': round(recall, 4),
            'f1_at_k': round(f1, 4),
            'mrr': round(mrr, 4),
            'avg_similarity_score': round(float(avg_score), 4),
            'retrieved_chunk_ids': retrieved_ids,
            'true_positives': tp,
            'total_relevant': len(relevant_set)
        }

    def format_context_for_llm(self, retrieved_docs: List[Dict]) -> str:
        """Format retrieved documents as context for LLM"""
        context_parts = []
        for i, doc in enumerate(retrieved_docs, start=1):
            context_parts.append(
                f"[Document {i}]\n"
                f"Topic: {doc['topic']} ({doc['domain']})\n"
                f"{doc['content']}\n"
            )
        return "\n".join(context_parts)


def test_retrieval_system():
    """Quick test of retrieval system"""
    print("\n" + "="*60)
    print("Testing RAG Retrieval System")
    print("="*60)

    # Initialize
    retriever = RetrievalSystem()

    # Test queries
    test_queries = [
        ("What is the capital of France?", [11]),
        ("Compare GPT-4 and Claude", [0, 1]),
        ("Tell me about vector databases", [3, 4]),
    ]

    for query, relevant_ids in test_queries:
        print(f"\n[QUERY] {query}")
        print(f"[GROUND TRUTH] {relevant_ids}")

        # Retrieve
        results = retriever.retrieve(query, top_k=3)

        print(f"\n[TOP 3 RESULTS]")
        for doc in results:
            marker = "[+]" if doc['chunk_id'] in relevant_ids else "[-]"
            print(f"  [{marker}] Chunk {doc['chunk_id']}: {doc['topic']} (score: {doc['score']:.3f})")
            print(f"      {doc['content'][:100]}...")

        # Evaluate
        metrics = retriever.evaluate_retrieval(query, relevant_ids, top_k=3)
        print(f"\n[METRICS]")
        print(f"  Precision@3: {metrics['precision_at_k']:.2%}")
        print(f"  Recall@3: {metrics['recall_at_k']:.2%}")
        print(f"  F1@3: {metrics['f1_at_k']:.2%}")
        print(f"  MRR: {metrics['mrr']:.3f}")

    print("\n" + "="*60)
    print("[OK] Retrieval system test complete!")
    print("="*60)


if __name__ == "__main__":
    test_retrieval_system()
