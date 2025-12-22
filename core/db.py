"""
Database models and utilities for the Eval Dashboard.
Uses SQLAlchemy ORM for database operations.
"""
import os
import json
import subprocess
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, relationship, Session, declarative_base

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/eval_dashboard.db")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Run(Base):
    """
    Represents a single evaluation run across all questions.
    """
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    commit_hash = Column(String(40), nullable=True)  # Git SHA
    total_cost = Column(Float, default=0.0)  # Estimated or actual cost
    avg_latency = Column(Float, default=0.0)  # Average latency in seconds
    accuracy = Column(Float, default=0.0)  # Average score (0.0 to 1.0)
    total_questions = Column(Integer, default=0)
    evaluation_time = Column(Float, default=0.0)  # Total time for this run in seconds

    # Relationship to evaluations
    evaluations = relationship("Evaluation", back_populates="run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Run(id={self.id}, model={self.model_name}, accuracy={self.accuracy:.2f}, timestamp={self.timestamp})>"


class Evaluation(Base):
    """
    Represents a single question evaluation within a run.
    """
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False, index=True)
    question_id = Column(String(50), nullable=False, index=True)
    category = Column(String(100), nullable=True, index=True)
    question_text = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    model_response = Column(Text, nullable=True)
    judge_score = Column(Float, nullable=False)  # 0.0 to 1.0
    judge_reasoning = Column(Text, nullable=True)
    latency = Column(Float, nullable=True)  # Response time in seconds
    cost = Column(Float, default=0.0)  # Estimated cost for this question
    image_path = Column(String(500), nullable=True)  # Path to image for vision questions

    # Relationship back to run
    run = relationship("Run", back_populates="evaluations")

    def __repr__(self):
        return f"<Evaluation(id={self.id}, run_id={self.run_id}, question_id={self.question_id}, score={self.judge_score})>"


class RAGRun(Base):
    """
    Represents a single RAG evaluation run across all RAG questions.
    """
    __tablename__ = "rag_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    commit_hash = Column(String(40), nullable=True)
    retrieval_k = Column(Integer, default=5)  # Top-K retrieval parameter

    # Aggregate retrieval metrics
    avg_precision = Column(Float, default=0.0)  # Average Precision@K
    avg_recall = Column(Float, default=0.0)  # Average Recall@K
    avg_f1 = Column(Float, default=0.0)  # Average F1@K
    avg_mrr = Column(Float, default=0.0)  # Average MRR

    # Aggregate answer metrics
    avg_answer_score = Column(Float, default=0.0)  # Answer correctness
    avg_grounding_score = Column(Float, default=0.0)  # Answer grounding

    # Performance metrics
    avg_retrieval_time = Column(Float, default=0.0)  # Avg retrieval time in seconds
    avg_generation_time = Column(Float, default=0.0)  # Avg generation time in seconds
    total_cost = Column(Float, default=0.0)  # Estimated total cost
    total_questions = Column(Integer, default=0)
    evaluation_time = Column(Float, default=0.0)  # Total evaluation time

    # Relationship to RAG evaluations
    evaluations = relationship("RAGEvaluation", back_populates="run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RAGRun(id={self.id}, model={self.model_name}, recall={self.avg_recall:.2f}, answer_score={self.avg_answer_score:.2f})>"


class RAGEvaluation(Base):
    """
    Represents a single RAG question evaluation within a run.
    """
    __tablename__ = "rag_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("rag_runs.id"), nullable=False, index=True)
    question_id = Column(String(50), nullable=False, index=True)
    category = Column(String(100), nullable=True, index=True)
    question_text = Column(Text, nullable=False)
    expected_answer = Column(Text, nullable=False)

    # Retrieval metrics
    retrieval_precision = Column(Float, default=0.0)
    retrieval_recall = Column(Float, default=0.0)
    retrieval_f1 = Column(Float, default=0.0)
    retrieval_mrr = Column(Float, default=0.0)
    retrieval_similarity_score = Column(Float, default=0.0)
    retrieved_chunk_ids = Column(String(500), nullable=True)  # JSON string of chunk IDs
    retrieval_time = Column(Float, default=0.0)

    # Generation
    generated_answer = Column(Text, nullable=True)
    generation_time = Column(Float, default=0.0)

    # Judging
    answer_score = Column(Float, default=0.0)  # 0.0 to 1.0
    answer_reasoning = Column(Text, nullable=True)
    grounding_score = Column(Float, default=0.0)  # 0.0 to 1.0
    grounding_reasoning = Column(Text, nullable=True)
    judge_time = Column(Float, default=0.0)

    # Costs
    cost = Column(Float, default=0.0)

    # Relationship back to run
    run = relationship("RAGRun", back_populates="evaluations")

    def __repr__(self):
        return f"<RAGEvaluation(id={self.id}, run_id={self.run_id}, question_id={self.question_id}, recall={self.retrieval_recall:.2f})>"


def init_db():
    """
    Initialize the database by creating all tables.
    Safe to call multiple times (won't recreate existing tables).
    """
    Base.metadata.create_all(bind=engine)
    print(f"[OK] Database initialized: {DATABASE_URL}")


def get_git_commit_hash() -> Optional[str]:
    """
    Get the current git commit hash (SHA).
    Returns None if not in a git repository or git is not available.
    """
    try:
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        return commit_hash
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def estimate_cost(model_name: str, response_length: int) -> float:
    """
    Rough cost estimation based on model and response length.
    This is a placeholder - replace with actual token-based pricing later.

    Args:
        model_name: Name of the model used
        response_length: Length of response in characters

    Returns:
        Estimated cost in USD
    """
    # Rough estimates per 1000 characters (very approximate)
    cost_per_1k_chars = {
        "gpt-4o": 0.005,
        "gpt-4o-mini": 0.0003,
        "gpt-5-chat": 0.006,
        "claude-opus": 0.015,
        "claude-sonnet": 0.003,
        "claude-haiku": 0.00025,
    }

    # Try to match model name to known pricing
    for key, price in cost_per_1k_chars.items():
        if key in model_name.lower():
            return (response_length / 1000) * price

    # Default fallback
    return (response_length / 1000) * 0.001


def save_run(
    model_name: str,
    results: List[Dict],
    evaluation_time: float,
    commit_hash: Optional[str] = None
) -> int:
    """
    Save a complete evaluation run to the database.

    Args:
        model_name: Name of the model evaluated
        results: List of evaluation result dictionaries
        evaluation_time: Total time taken for evaluation in seconds
        commit_hash: Git commit hash (optional, will auto-detect if None)

    Returns:
        The ID of the created run
    """
    db: Session = SessionLocal()

    try:
        # Auto-detect commit hash if not provided
        if commit_hash is None:
            commit_hash = get_git_commit_hash()

        # Calculate aggregate metrics
        total_questions = len(results)
        scores = [r.get("score", 0.0) for r in results]
        latencies = [r.get("latency", 0.0) for r in results if r.get("latency") is not None]

        accuracy = sum(scores) / total_questions if total_questions > 0 else 0.0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        # Estimate total cost
        total_cost = sum(
            estimate_cost(model_name, len(r.get("model_response", "") or ""))
            for r in results
        )

        # Create run record
        run = Run(
            model_name=model_name,
            timestamp=datetime.utcnow(),
            commit_hash=commit_hash,
            total_cost=total_cost,
            avg_latency=avg_latency,
            accuracy=accuracy,
            total_questions=total_questions,
            evaluation_time=evaluation_time
        )

        db.add(run)
        db.flush()  # Get the run ID

        # Create evaluation records
        for result in results:
            eval_record = Evaluation(
                run_id=run.id,
                question_id=result.get("id", ""),
                category=result.get("category", ""),
                question_text=result.get("input", ""),
                expected_output=result.get("expected_output", ""),
                model_response=result.get("model_response", ""),
                judge_score=result.get("score", 0.0),
                judge_reasoning=result.get("reasoning", ""),
                latency=result.get("latency"),
                cost=estimate_cost(model_name, len(result.get("model_response", "") or "")),
                image_path=result.get("image_path")
            )
            db.add(eval_record)

        db.commit()
        print(f"[OK] Saved run {run.id} for {model_name} (accuracy: {accuracy:.2%}, cost: ${total_cost:.4f})")
        return run.id

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error saving run: {e}")
        raise
    finally:
        db.close()


def get_run_by_id(run_id: int) -> Optional[Run]:
    """
    Retrieve a specific run by ID with all its evaluations.
    """
    db: Session = SessionLocal()
    try:
        from sqlalchemy.orm import joinedload
        return db.query(Run).options(joinedload(Run.evaluations)).filter(Run.id == run_id).first()
    finally:
        db.close()


def get_recent_runs(limit: int = 10) -> List[Run]:
    """
    Get the most recent evaluation runs.
    """
    db: Session = SessionLocal()
    try:
        return db.query(Run).order_by(Run.timestamp.desc()).limit(limit).all()
    finally:
        db.close()


def get_runs_by_model(model_name: str) -> List[Run]:
    """
    Get all runs for a specific model, ordered by timestamp.
    """
    db: Session = SessionLocal()
    try:
        return db.query(Run).filter(Run.model_name == model_name).order_by(Run.timestamp.desc()).all()
    finally:
        db.close()


def get_drift_analysis(model_name: str, threshold: float = 0.05) -> Tuple[Optional[Run], Optional[Run], bool]:
    """
    Analyze drift for a model by comparing latest run to best historical run.

    Args:
        model_name: Model to analyze
        threshold: Accuracy drop threshold (default 5%)

    Returns:
        Tuple of (latest_run, best_run, has_drifted)
    """
    db: Session = SessionLocal()
    try:
        runs = db.query(Run).filter(Run.model_name == model_name).order_by(Run.timestamp.desc()).all()

        if not runs:
            return None, None, False

        latest_run = runs[0]
        best_run = max(runs, key=lambda r: r.accuracy)

        accuracy_drop = best_run.accuracy - latest_run.accuracy
        has_drifted = accuracy_drop > threshold

        return latest_run, best_run, has_drifted

    finally:
        db.close()


def save_rag_run(
    model_name: str,
    results: List[Dict],
    retrieval_k: int,
    evaluation_time: float,
    commit_hash: Optional[str] = None
) -> int:
    """
    Save a complete RAG evaluation run to the database.

    Args:
        model_name: Name of the model evaluated
        results: List of RAG evaluation result dictionaries
        retrieval_k: Top-K retrieval parameter used
        evaluation_time: Total time taken for evaluation in seconds
        commit_hash: Git commit hash (optional, will auto-detect if None)

    Returns:
        The ID of the created RAG run
    """
    db: Session = SessionLocal()

    try:
        # Auto-detect commit hash if not provided
        if commit_hash is None:
            commit_hash = get_git_commit_hash()

        # Calculate aggregate metrics
        total_questions = len(results)

        # Retrieval metrics
        precisions = [r.get("retrieval_precision", 0.0) for r in results]
        recalls = [r.get("retrieval_recall", 0.0) for r in results]
        f1s = [r.get("retrieval_f1", 0.0) for r in results]
        mrrs = [r.get("retrieval_mrr", 0.0) for r in results]

        avg_precision = sum(precisions) / total_questions if total_questions > 0 else 0.0
        avg_recall = sum(recalls) / total_questions if total_questions > 0 else 0.0
        avg_f1 = sum(f1s) / total_questions if total_questions > 0 else 0.0
        avg_mrr = sum(mrrs) / total_questions if total_questions > 0 else 0.0

        # Answer metrics
        answer_scores = [r.get("answer_score", 0.0) for r in results]
        grounding_scores = [r.get("grounding_score", 0.0) for r in results]

        avg_answer_score = sum(answer_scores) / total_questions if total_questions > 0 else 0.0
        avg_grounding_score = sum(grounding_scores) / total_questions if total_questions > 0 else 0.0

        # Time metrics
        retrieval_times = [r.get("retrieval_time", 0.0) for r in results]
        generation_times = [r.get("generation_time", 0.0) for r in results]

        avg_retrieval_time = sum(retrieval_times) / len(retrieval_times) if retrieval_times else 0.0
        avg_generation_time = sum(generation_times) / len(generation_times) if generation_times else 0.0

        # Estimate total cost
        total_cost = sum(estimate_cost(model_name, len(r.get("generated_answer", "") or "")) for r in results)

        # Create RAG run record
        rag_run = RAGRun(
            model_name=model_name,
            timestamp=datetime.utcnow(),
            commit_hash=commit_hash,
            retrieval_k=retrieval_k,
            avg_precision=avg_precision,
            avg_recall=avg_recall,
            avg_f1=avg_f1,
            avg_mrr=avg_mrr,
            avg_answer_score=avg_answer_score,
            avg_grounding_score=avg_grounding_score,
            avg_retrieval_time=avg_retrieval_time,
            avg_generation_time=avg_generation_time,
            total_cost=total_cost,
            total_questions=total_questions,
            evaluation_time=evaluation_time
        )

        db.add(rag_run)
        db.flush()  # Get the run ID

        # Create RAG evaluation records
        for result in results:
            # Convert retrieved_chunk_ids list to JSON string
            retrieved_ids = result.get("retrieved_chunk_ids", [])
            retrieved_ids_json = json.dumps(retrieved_ids) if retrieved_ids else "[]"

            eval_record = RAGEvaluation(
                run_id=rag_run.id,
                question_id=result.get("question_id", ""),
                category=result.get("category", ""),
                question_text=result.get("question", ""),
                expected_answer=result.get("expected_answer", ""),
                retrieval_precision=result.get("retrieval_precision", 0.0),
                retrieval_recall=result.get("retrieval_recall", 0.0),
                retrieval_f1=result.get("retrieval_f1", 0.0),
                retrieval_mrr=result.get("retrieval_mrr", 0.0),
                retrieval_similarity_score=result.get("retrieval_similarity_score", 0.0),
                retrieved_chunk_ids=retrieved_ids_json,
                retrieval_time=result.get("retrieval_time", 0.0),
                generated_answer=result.get("generated_answer", ""),
                generation_time=result.get("generation_time", 0.0),
                answer_score=result.get("answer_score", 0.0),
                answer_reasoning=result.get("answer_reasoning", ""),
                grounding_score=result.get("grounding_score", 0.0),
                grounding_reasoning=result.get("grounding_reasoning", ""),
                judge_time=result.get("judge_time", 0.0),
                cost=estimate_cost(model_name, len(result.get("generated_answer", "") or ""))
            )
            db.add(eval_record)

        db.commit()
        print(f"[OK] Saved RAG run {rag_run.id} for {model_name} (recall: {avg_recall:.2%}, answer_score: {avg_answer_score:.2%})")
        return rag_run.id

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error saving RAG run: {e}")
        raise
    finally:
        db.close()


def get_rag_run_by_id(run_id: int) -> Optional[RAGRun]:
    """
    Retrieve a specific RAG run by ID with all its evaluations.
    """
    db: Session = SessionLocal()
    try:
        from sqlalchemy.orm import joinedload
        return db.query(RAGRun).options(joinedload(RAGRun.evaluations)).filter(RAGRun.id == run_id).first()
    finally:
        db.close()


def get_recent_rag_runs(limit: int = 10) -> List[RAGRun]:
    """
    Get the most recent RAG evaluation runs.
    """
    db: Session = SessionLocal()
    try:
        return db.query(RAGRun).order_by(RAGRun.timestamp.desc()).limit(limit).all()
    finally:
        db.close()


def get_rag_runs_by_model(model_name: str) -> List[RAGRun]:
    """
    Get all RAG runs for a specific model, ordered by timestamp.
    """
    db: Session = SessionLocal()
    try:
        return db.query(RAGRun).filter(RAGRun.model_name == model_name).order_by(RAGRun.timestamp.desc()).all()
    finally:
        db.close()


def get_rag_drift_analysis(model_name: str, threshold: float = 0.05) -> Tuple[Optional[RAGRun], Optional[RAGRun], bool]:
    """
    Analyze RAG drift for a model by comparing latest run to best historical run.

    Args:
        model_name: Model to analyze
        threshold: Recall drop threshold (default 5%)

    Returns:
        Tuple of (latest_run, best_run, has_drifted)
    """
    db: Session = SessionLocal()
    try:
        runs = db.query(RAGRun).filter(RAGRun.model_name == model_name).order_by(RAGRun.timestamp.desc()).all()

        if not runs:
            return None, None, False

        latest_run = runs[0]
        # Use avg_recall as primary metric for RAG drift
        best_run = max(runs, key=lambda r: r.avg_recall)

        recall_drop = best_run.avg_recall - latest_run.avg_recall
        has_drifted = recall_drop > threshold

        return latest_run, best_run, has_drifted

    finally:
        db.close()


if __name__ == "__main__":
    # Initialize database when run directly
    init_db()
    print("Database tables created successfully!")
