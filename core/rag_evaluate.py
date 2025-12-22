"""
RAG Evaluation Pipeline
Evaluates retrieval quality AND generation quality for RAG systems
"""

import os
import csv
import json
import ast
import requests
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv

from retrieval import RetrievalSystem
from db import save_rag_run, init_db

load_dotenv()

# Initialize database
init_db()


class RAGEvaluator:
    """Complete RAG evaluation pipeline"""

    def __init__(
        self,
        dataset_path: str = "data/golden_dataset_rag.csv",
        retrieval_k: int = 5,
        model: str = "gpt-4o-mini"
    ):
        """
        Initialize RAG evaluator

        Args:
            dataset_path: Path to RAG evaluation dataset
            retrieval_k: Number of documents to retrieve per question
            model: Model to use for generation
        """
        self.dataset_path = dataset_path
        self.retrieval_k = retrieval_k
        self.model = model

        # Initialize components
        self.retriever = RetrievalSystem()

        # LiteLLM proxy handles actual provider API keys from .env
        # OpenAI SDK configured to use LiteLLM proxy (matches existing architecture)
        self.client = OpenAI(
            api_key="sk-test",  # placeholder for LiteLLM proxy
            base_url="http://127.0.0.1:4000"  # LiteLLM proxy endpoint
        )

        # Check if LiteLLM proxy is available
        self._check_litellm_proxy()

        # Load dataset
        self.questions = self._load_dataset()

        print(f"[OK] RAG Evaluator initialized")
        print(f"  Dataset: {len(self.questions)} questions")
        print(f"  Retrieval: Top-{retrieval_k}")
        print(f"  Model: {model}")

    def _check_litellm_proxy(self):
        """Check if LiteLLM proxy is available"""
        try:
            response = requests.get("http://127.0.0.1:4000/health", timeout=5)
            if response.status_code == 200:
                print("[OK] LiteLLM proxy is running")
            else:
                print("[WARNING] LiteLLM proxy responded but may not be healthy")
        except requests.exceptions.RequestException as e:
            print(f"\n[WARNING] Could not verify LiteLLM proxy health: {type(e).__name__}")
            print("Continuing anyway... If you see connection errors, make sure LiteLLM is running.")
            print("The proxy should be running on http://127.0.0.1:4000\n")

    def _load_dataset(self) -> List[Dict]:
        """Load RAG evaluation dataset from CSV"""
        questions = []
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse relevant_chunk_ids as list
                try:
                    relevant_ids = ast.literal_eval(row['relevant_chunk_ids'])
                    # Ensure it's a list (sometimes it's parsed as int)
                    if isinstance(relevant_ids, int):
                        relevant_ids = [relevant_ids]
                    elif not isinstance(relevant_ids, list):
                        relevant_ids = []
                except Exception as e:
                    print(f"[WARNING] Failed to parse relevant_chunk_ids for Q{row['id']}: {e}")
                    relevant_ids = []

                questions.append({
                    'id': row['id'],
                    'category': row['category'],
                    'question': row['input'],
                    'expected_answer': row['expected_output'],
                    'relevant_chunk_ids': relevant_ids,
                    'notes': row.get('notes', '')
                })

        return questions

    def evaluate_single_question(
        self,
        question_data: Dict,
        save_traces: bool = True
    ) -> Dict:
        """
        Evaluate a single RAG question

        Returns:
            Dict with retrieval metrics and generation metrics
        """
        question_id = question_data['id']
        question = question_data['question']
        expected_answer = question_data['expected_answer']
        relevant_chunk_ids = question_data['relevant_chunk_ids']

        # Step 1: Retrieval
        start_time = datetime.now()
        retrieved_docs = self.retriever.retrieve(question, top_k=self.retrieval_k)
        retrieval_time = (datetime.now() - start_time).total_seconds()

        # Evaluate retrieval quality
        retrieval_metrics = self.retriever.evaluate_retrieval(
            question,
            relevant_chunk_ids,
            top_k=self.retrieval_k
        )

        # Step 2: Format context for LLM
        context = self.retriever.format_context_for_llm(retrieved_docs)

        # Step 3: Generate answer with context
        start_time = datetime.now()
        generated_answer = self._generate_answer(question, context)
        generation_time = (datetime.now() - start_time).total_seconds()

        # Step 4: Judge the answer quality
        start_time = datetime.now()
        judge_score, judge_reasoning = self._judge_answer(generated_answer, expected_answer)
        judge_time = (datetime.now() - start_time).total_seconds()

        # Step 5: Judge answer grounding (does answer use context?)
        grounding_score, grounding_reasoning = self._judge_grounding(
            question, context, generated_answer
        )

        # Combine results
        result = {
            # Question metadata
            'question_id': question_id,
            'category': question_data['category'],
            'question': question,
            'expected_answer': expected_answer,

            # Retrieval results
            'retrieved_chunk_ids': retrieval_metrics['retrieved_chunk_ids'],
            'retrieval_precision': retrieval_metrics['precision_at_k'],
            'retrieval_recall': retrieval_metrics['recall_at_k'],
            'retrieval_f1': retrieval_metrics['f1_at_k'],
            'retrieval_mrr': retrieval_metrics['mrr'],
            'retrieval_similarity_score': retrieval_metrics['avg_similarity_score'],
            'retrieval_time': round(retrieval_time, 3),

            # Generation results
            'generated_answer': generated_answer,
            'generation_time': round(generation_time, 3),

            # Answer quality
            'answer_score': judge_score,
            'answer_reasoning': judge_reasoning,
            'judge_time': round(judge_time, 3),

            # Grounding
            'grounding_score': grounding_score,
            'grounding_reasoning': grounding_reasoning,

            # Total
            'total_time': round(retrieval_time + generation_time + judge_time, 3),

            # Retrieved context (for debugging)
            'retrieved_docs': retrieved_docs if save_traces else None
        }

        return result

    def _judge_answer(self, answer: str, expected_answer: str) -> tuple[float, str]:
        """
        Judge answer quality against expected answer

        Returns:
            (score, reasoning)
        """
        prompt = f"""Rate the correctness of the answer compared to the expected answer.

Expected answer: {expected_answer}
Model answer: {answer}

Task:
1. Check if the answer is factually correct
2. Allow for paraphrasing and different wording
3. Rate on a scale of 0-1:
   - 1.0 = Completely correct
   - 0.7 = Mostly correct with minor issues
   - 0.5 = Partially correct
   - 0.3 = Mostly incorrect
   - 0.0 = Completely incorrect or irrelevant

Respond ONLY in this format:
SCORE: <0.0-1.0>
REASONING: <brief explanation>"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=300
            )

            content = response.choices[0].message.content.strip()

            # Parse response
            lines = content.split('\n')
            score = 0.0
            reasoning = ""

            for line in lines:
                if line.startswith('SCORE:'):
                    try:
                        score = float(line.split('SCORE:')[1].strip())
                    except:
                        score = 0.0
                elif line.startswith('REASONING:'):
                    reasoning = line.split('REASONING:')[1].strip()

            return score, reasoning

        except Exception as e:
            return 0.0, f"Error judging answer: {str(e)}"

    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using retrieved context"""
        prompt = f"""Answer the question using ONLY the information provided in the context below.
If the context does not contain enough information to answer the question, say "Not mentioned in the provided context."

Context:
{context}

Question: {question}

Answer:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[ERROR: {str(e)}]"

    def _judge_grounding(
        self,
        question: str,
        context: str,
        answer: str
    ) -> tuple[float, str]:
        """
        Judge if the answer is grounded in the provided context

        Returns:
            (grounding_score, reasoning)
        """
        prompt = f"""Evaluate if the answer is grounded in the provided context.

Question: {question}

Context:
{context}

Answer: {answer}

Task:
1. Check if the answer's key claims can be verified using the context
2. Identify any hallucinations or information not present in context
3. Rate grounding on a scale of 0-1:
   - 1.0 = Fully grounded, all claims supported by context
   - 0.7 = Mostly grounded, minor details not in context
   - 0.5 = Partially grounded, some unsupported claims
   - 0.3 = Poorly grounded, mostly unsupported
   - 0.0 = Not grounded, hallucinated or irrelevant

Respond ONLY in this format:
SCORE: <0.0-1.0>
REASONING: <brief explanation>"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Use same judge model
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=300
            )

            content = response.choices[0].message.content.strip()

            # Parse response
            lines = content.split('\n')
            score = 0.0
            reasoning = ""

            for line in lines:
                if line.startswith('SCORE:'):
                    try:
                        score = float(line.split('SCORE:')[1].strip())
                    except:
                        score = 0.0
                elif line.startswith('REASONING:'):
                    reasoning = line.split('REASONING:')[1].strip()

            return score, reasoning

        except Exception as e:
            return 0.0, f"Error judging grounding: {str(e)}"

    def evaluate_all(
        self,
        parallel: bool = True,
        max_workers: int = 5,
        output_dir: str = "results/rag",
        save_to_db: bool = True
    ) -> Dict:
        """
        Evaluate all questions in dataset

        Args:
            parallel: Run evaluations in parallel
            max_workers: Max parallel workers
            output_dir: Directory to save results
            save_to_db: Save results to database

        Returns:
            Summary statistics
        """
        print(f"\n{'='*60}")
        print(f"RAG Evaluation: {self.model}")
        print(f"{'='*60}")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        results = []
        start_time = datetime.now()

        if parallel:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.evaluate_single_question, q): q
                    for q in self.questions
                }

                for i, future in enumerate(as_completed(futures), 1):
                    try:
                        result = future.result()
                        results.append(result)
                        print(f"[{i}/{len(self.questions)}] Q{result['question_id']}: "
                              f"Retrieval P={result['retrieval_precision']:.2f} "
                              f"R={result['retrieval_recall']:.2f} | "
                              f"Answer={result['answer_score']:.2f} "
                              f"Grounding={result['grounding_score']:.2f}")
                    except Exception as e:
                        question_data = futures[future]
                        print(f"[ERROR] Q{question_data['id']} failed: {str(e)}")
                        print(f"[INFO] Continuing with remaining questions...")
                        # Continue processing other questions
        else:
            for i, question_data in enumerate(self.questions, 1):
                result = self.evaluate_single_question(question_data)
                results.append(result)
                print(f"[{i}/{len(self.questions)}] Q{result['question_id']}: "
                      f"Retrieval P={result['retrieval_precision']:.2f} "
                      f"R={result['retrieval_recall']:.2f} | "
                      f"Answer={result['answer_score']:.2f} "
                      f"Grounding={result['grounding_score']:.2f}")

        evaluation_time = (datetime.now() - start_time).total_seconds()

        # Compute summary statistics
        summary = self._compute_summary(results)

        # Save to database
        if save_to_db:
            try:
                run_id = save_rag_run(
                    model_name=self.model,
                    results=results,
                    retrieval_k=self.retrieval_k,
                    evaluation_time=evaluation_time
                )
                print(f"\n[OK] Saved to database as RAG run #{run_id}")
            except Exception as e:
                print(f"\n[WARNING] Failed to save to database: {e}")

        # Save results to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"{output_dir}/rag_eval_{self.model}_{timestamp}.json"

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'model': self.model,
                'retrieval_k': self.retrieval_k,
                'timestamp': timestamp,
                'summary': summary,
                'results': results
            }, f, indent=2, ensure_ascii=False)

        print(f"\n[OK] Results saved to {results_file}")

        return summary

    def _compute_summary(self, results: List[Dict]) -> Dict:
        """Compute aggregate statistics"""
        if not results:
            return {}

        # Retrieval metrics
        avg_precision = sum(r['retrieval_precision'] for r in results) / len(results)
        avg_recall = sum(r['retrieval_recall'] for r in results) / len(results)
        avg_f1 = sum(r['retrieval_f1'] for r in results) / len(results)
        avg_mrr = sum(r['retrieval_mrr'] for r in results) / len(results)

        # Answer metrics
        avg_answer_score = sum(r['answer_score'] for r in results) / len(results)
        avg_grounding = sum(r['grounding_score'] for r in results) / len(results)

        # Time metrics
        avg_retrieval_time = sum(r['retrieval_time'] for r in results) / len(results)
        avg_generation_time = sum(r['generation_time'] for r in results) / len(results)
        avg_total_time = sum(r['total_time'] for r in results) / len(results)

        # Category breakdown
        category_stats = {}
        for result in results:
            cat = result['category']
            if cat not in category_stats:
                category_stats[cat] = {
                    'count': 0,
                    'retrieval_precision': [],
                    'retrieval_recall': [],
                    'answer_score': [],
                    'grounding_score': []
                }
            category_stats[cat]['count'] += 1
            category_stats[cat]['retrieval_precision'].append(result['retrieval_precision'])
            category_stats[cat]['retrieval_recall'].append(result['retrieval_recall'])
            category_stats[cat]['answer_score'].append(result['answer_score'])
            category_stats[cat]['grounding_score'].append(result['grounding_score'])

        # Compute category averages
        for cat in category_stats:
            stats = category_stats[cat]
            stats['avg_retrieval_precision'] = sum(stats['retrieval_precision']) / stats['count']
            stats['avg_retrieval_recall'] = sum(stats['retrieval_recall']) / stats['count']
            stats['avg_answer_score'] = sum(stats['answer_score']) / stats['count']
            stats['avg_grounding_score'] = sum(stats['grounding_score']) / stats['count']
            # Remove raw lists to reduce output size
            del stats['retrieval_precision']
            del stats['retrieval_recall']
            del stats['answer_score']
            del stats['grounding_score']

        summary = {
            'total_questions': len(results),
            'retrieval_metrics': {
                'avg_precision_at_k': round(avg_precision, 4),
                'avg_recall_at_k': round(avg_recall, 4),
                'avg_f1_at_k': round(avg_f1, 4),
                'avg_mrr': round(avg_mrr, 4)
            },
            'answer_metrics': {
                'avg_answer_score': round(avg_answer_score, 4),
                'avg_grounding_score': round(avg_grounding, 4)
            },
            'time_metrics': {
                'avg_retrieval_time': round(avg_retrieval_time, 3),
                'avg_generation_time': round(avg_generation_time, 3),
                'avg_total_time': round(avg_total_time, 3)
            },
            'category_breakdown': category_stats
        }

        # Print summary
        print(f"\n{'='*60}")
        print("SUMMARY STATISTICS")
        print(f"{'='*60}")
        print(f"Total Questions: {summary['total_questions']}")
        print(f"\nRetrieval Performance:")
        print(f"  Precision@{self.retrieval_k}: {avg_precision:.2%}")
        print(f"  Recall@{self.retrieval_k}: {avg_recall:.2%}")
        print(f"  F1@{self.retrieval_k}: {avg_f1:.2%}")
        print(f"  MRR: {avg_mrr:.3f}")
        print(f"\nAnswer Quality:")
        print(f"  Avg Answer Score: {avg_answer_score:.2%}")
        print(f"  Avg Grounding Score: {avg_grounding:.2%}")
        print(f"\nPerformance:")
        print(f"  Avg Retrieval Time: {avg_retrieval_time:.2f}s")
        print(f"  Avg Generation Time: {avg_generation_time:.2f}s")
        print(f"  Avg Total Time: {avg_total_time:.2f}s")
        print(f"{'='*60}")

        return summary


def main():
    """Test RAG evaluation on a subset"""
    print("\n" + "="*60)
    print("RAG EVALUATION TEST")
    print("="*60)
    print("This will evaluate the first 10 questions to validate the system.")
    print("For production runs, edit this file or import RAGEvaluator directly.")
    print("="*60 + "\n")

    evaluator = RAGEvaluator(
        dataset_path="data/golden_dataset_rag.csv",
        retrieval_k=5,
        model="gpt-4o-mini"
    )

    # Test on first 10 questions
    print("\n[TEST MODE] Evaluating first 10 questions...")
    evaluator.questions = evaluator.questions[:10]

    # Use sequential processing for test mode (more reliable)
    summary = evaluator.evaluate_all(
        parallel=False,  # Sequential for easier debugging
        max_workers=3
    )


if __name__ == "__main__":
    main()
