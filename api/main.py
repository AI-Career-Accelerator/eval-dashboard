"""
FastAPI backend for Eval Dashboard.
Enhanced API with background tasks, webhook callbacks, and comprehensive endpoints.
"""
import os
import sys
import uuid
import requests
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import (
    RunEvaluationRequest,
    BackgroundTaskResponse,
    RunSummary,
    RunDetail,
    RunListResponse,
    EvaluationDetail,
    ModelsResponse,
    ModelStats,
    DriftAnalysis,
    DashboardStats,
    HealthResponse,
    RAGRunSummary,
    RAGRunDetail,
    RAGRunListResponse,
    RAGEvaluationDetail,
    RAGDriftAnalysis
)
from api.background import run_evaluation_task
from core.db import (
    init_db,
    get_run_by_id,
    get_recent_runs,
    get_runs_by_model,
    get_drift_analysis,
    get_rag_run_by_id,
    get_recent_rag_runs,
    get_rag_runs_by_model,
    get_rag_drift_analysis,
    SessionLocal,
    Run,
    Evaluation,
    RAGRun,
    RAGEvaluation
)
from core.drift_detector import DriftDetector
from sqlalchemy import func, desc, text
from sqlalchemy.orm import joinedload


# Initialize FastAPI app
app = FastAPI(
    title="Eval Dashboard API",
    description="REST API for AI model evaluation tracking and drift detection",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    init_db()
    print("[API] Database initialized")


# Available models (from evaluate.py)
AVAILABLE_MODELS = [
    "gpt-5-chat",
    "gpt-4o",
    "gpt-4o-mini",
    "claude-opus-4-5",
    "claude-sonnet-4-5",
    "claude-haiku-4-5",
    "Kimi-K2-Thinking",
    "DeepSeek-V3.1",
    "grok-3",
    "Mistral-Large-3",
    "Llama-4-Maverick-17B-128E-Instruct-FP8"
]


# ============================================================================
# CORE ENDPOINTS
# ============================================================================

@app.post("/run-evaluation", response_model=BackgroundTaskResponse)
async def run_evaluation(
    request: RunEvaluationRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger a new evaluation run in the background.

    - **models**: List of models to evaluate (defaults to all if not provided)
    - **webhook_url**: Optional callback URL to receive results when complete
    - **max_questions**: Optional limit on questions (for testing)

    Returns a job ID immediately. Results will be sent to webhook_url when complete.
    """
    # Use provided models or default to all
    models_to_evaluate = request.models if request.models else AVAILABLE_MODELS

    # Validate model names
    invalid_models = [m for m in models_to_evaluate if m not in AVAILABLE_MODELS]
    if invalid_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid models: {invalid_models}. Available: {AVAILABLE_MODELS}"
        )

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Add background task
    background_tasks.add_task(
        run_evaluation_task,
        models=models_to_evaluate,
        webhook_url=str(request.webhook_url) if request.webhook_url else None,
        max_questions=request.max_questions,
        job_id=job_id
    )

    return BackgroundTaskResponse(
        message="Evaluation started in background",
        job_id=job_id,
        webhook_url=str(request.webhook_url) if request.webhook_url else None,
        models=models_to_evaluate
    )


@app.get("/runs", response_model=RunListResponse)
async def get_runs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    model: Optional[str] = Query(None, description="Filter by model name"),
    min_accuracy: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum accuracy threshold")
):
    """
    Get paginated list of evaluation runs with optional filters.

    - **page**: Page number (starts at 1)
    - **page_size**: Number of results per page (max 100)
    - **model**: Filter by specific model name
    - **min_accuracy**: Filter runs with accuracy >= this value
    """
    db = SessionLocal()
    try:
        # Build query
        query = db.query(Run)

        # Apply filters
        if model:
            query = query.filter(Run.model_name == model)
        if min_accuracy is not None:
            query = query.filter(Run.accuracy >= min_accuracy)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        runs = query.order_by(desc(Run.timestamp)).offset(offset).limit(page_size).all()

        return RunListResponse(
            total=total,
            page=page,
            page_size=page_size,
            runs=[RunSummary.model_validate(run) for run in runs]
        )

    finally:
        db.close()


@app.get("/run/{run_id}", response_model=RunDetail)
async def get_run_detail(run_id: int):
    """
    Get detailed results for a specific run including all evaluations.

    - **run_id**: Unique identifier for the run

    Returns full run details with per-question breakdown and category analysis.
    """
    run = get_run_by_id(run_id)

    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    # Calculate category breakdown
    category_breakdown = {}
    for eval in run.evaluations:
        cat = eval.category
        if cat not in category_breakdown:
            category_breakdown[cat] = {
                "total_questions": 0,
                "avg_score": 0.0,
                "scores": []
            }
        category_breakdown[cat]["total_questions"] += 1
        category_breakdown[cat]["scores"].append(eval.judge_score)

    # Calculate averages
    for cat, data in category_breakdown.items():
        data["avg_score"] = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0.0
        del data["scores"]  # Remove scores list from response

    return RunDetail(
        run=RunSummary.model_validate(run),
        evaluations=[EvaluationDetail.model_validate(e) for e in run.evaluations],
        category_breakdown=category_breakdown
    )


# ============================================================================
# ENHANCED ENDPOINTS
# ============================================================================

@app.get("/models", response_model=ModelsResponse)
async def get_models(
    days: Optional[int] = Query(None, ge=1, description="Filter runs from last N days (e.g., 7, 30). None = all time")
):
    """
    Get statistics for all available models.

    Returns aggregate metrics across all historical runs for each model.

    - **days**: Optional filter to only include runs from the last N days
    """
    db = SessionLocal()
    try:
        from datetime import timedelta

        model_stats = []

        for model_name in AVAILABLE_MODELS:
            query = db.query(Run).filter(Run.model_name == model_name)

            # Apply time filter if specified
            if days:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(Run.timestamp >= cutoff_date)

            runs = query.all()

            if not runs:
                # Model hasn't been evaluated yet (or not in time period)
                model_stats.append(ModelStats(
                    model_name=model_name,
                    total_runs=0,
                    avg_accuracy=0.0,
                    best_accuracy=0.0,
                    worst_accuracy=0.0,
                    avg_cost=0.0,
                    avg_latency=0.0,
                    last_run_timestamp=None
                ))
                continue

            accuracies = [r.accuracy for r in runs]
            costs = [r.total_cost for r in runs]
            latencies = [r.avg_latency for r in runs]

            model_stats.append(ModelStats(
                model_name=model_name,
                total_runs=len(runs),
                avg_accuracy=sum(accuracies) / len(accuracies),
                best_accuracy=max(accuracies),
                worst_accuracy=min(accuracies),
                avg_cost=sum(costs) / len(costs),
                avg_latency=sum(latencies) / len(latencies),
                last_run_timestamp=max(r.timestamp for r in runs)
            ))

        # Sort by average accuracy (descending)
        model_stats.sort(key=lambda x: x.avg_accuracy, reverse=True)

        return ModelsResponse(models=model_stats)

    finally:
        db.close()


@app.get("/drift/{model_name}", response_model=DriftAnalysis)
async def get_drift(
    model_name: str,
    threshold: float = Query(0.05, ge=0.0, le=1.0, description="Accuracy drop threshold")
):
    """
    Analyze drift for a specific model.

    Compares latest run to best historical run to detect accuracy degradation.

    - **model_name**: Name of the model to analyze
    - **threshold**: Accuracy drop threshold (default 5%)

    Returns drift status and comparison between latest and best runs.
    """
    if model_name not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model: {model_name}. Available: {AVAILABLE_MODELS}"
        )

    latest_run, best_run, has_drifted = get_drift_analysis(model_name, threshold)

    if not latest_run:
        raise HTTPException(
            status_code=404,
            detail=f"No evaluation runs found for model: {model_name}"
        )

    accuracy_drop = (best_run.accuracy - latest_run.accuracy) if best_run else 0.0

    return DriftAnalysis(
        model_name=model_name,
        latest_run=RunSummary.model_validate(latest_run) if latest_run else None,
        best_run=RunSummary.model_validate(best_run) if best_run else None,
        has_drifted=has_drifted,
        accuracy_drop=accuracy_drop,
        threshold=threshold
    )


@app.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """
    Get overall dashboard statistics.

    Returns aggregate metrics across all models and runs for dashboard display.
    """
    db = SessionLocal()
    try:
        # Total counts
        total_runs = db.query(func.count(Run.id)).scalar()
        total_evaluations = db.query(func.count(Evaluation.id)).scalar()

        # Count unique models that have been evaluated
        total_models = db.query(func.count(func.distinct(Run.model_name))).scalar()

        # Recent runs (last 10)
        recent_runs = db.query(Run).order_by(desc(Run.timestamp)).limit(10).all()

        # Top models by average accuracy
        model_stats_query = db.query(
            Run.model_name,
            func.avg(Run.accuracy).label('avg_accuracy'),
            func.count(Run.id).label('total_runs'),
            func.avg(Run.total_cost).label('avg_cost'),
            func.avg(Run.avg_latency).label('avg_latency'),
            func.max(Run.timestamp).label('last_run')
        ).group_by(Run.model_name).all()

        top_models = [
            ModelStats(
                model_name=row.model_name,
                total_runs=row.total_runs,
                avg_accuracy=row.avg_accuracy,
                best_accuracy=0.0,  # Simplified for stats endpoint
                worst_accuracy=0.0,
                avg_cost=row.avg_cost,
                avg_latency=row.avg_latency,
                last_run_timestamp=row.last_run
            )
            for row in model_stats_query
        ]

        # Sort by accuracy
        top_models.sort(key=lambda x: x.avg_accuracy, reverse=True)
        top_models = top_models[:10]  # Top 10 models

        return DashboardStats(
            total_runs=total_runs,
            total_evaluations=total_evaluations,
            total_models=total_models,
            recent_runs=[RunSummary.model_validate(run) for run in recent_runs],
            top_models=top_models
        )

    finally:
        db.close()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring.

    Checks database connectivity and LiteLLM proxy availability.
    """
    # Check database
    db_connected = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_connected = True
    except Exception:
        pass

    # Check LiteLLM proxy
    litellm_available = False
    try:
        response = requests.get("http://127.0.0.1:4000/health", timeout=10)
        litellm_available = response.status_code == 200
    except Exception:
        pass

    status = "healthy" if (db_connected and litellm_available) else "degraded"

    return HealthResponse(
        status=status,
        timestamp=datetime.utcnow(),
        database_connected=db_connected,
        litellm_proxy_available=litellm_available
    )


# ============================================================================
# DRIFT DETECTION & ALERTS
# ============================================================================

@app.post("/test-alerts/{model_name}")
async def test_alerts(
    model_name: str,
    threshold: float = Query(5.0, ge=0.0, le=100.0, description="Drift threshold percentage")
):
    """
    Test drift detection and alerting for a specific model.

    Manually triggers drift check and sends alerts if drift is detected.

    - **model_name**: Name of the model to check
    - **threshold**: Drift threshold in percentage (default 5%)

    Returns drift status and alert delivery results.
    """
    if model_name not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model: {model_name}. Available: {AVAILABLE_MODELS}"
        )

    try:
        detector = DriftDetector(threshold_percent=threshold)
        result = detector.process_run(model_name)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing drift detection: {str(e)}"
        )


# ============================================================================
# RAG ENDPOINTS
# ============================================================================

@app.get("/rag-runs", response_model=RAGRunListResponse)
async def get_rag_runs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    model: Optional[str] = Query(None, description="Filter by model name"),
    min_recall: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum recall threshold")
):
    """
    Get paginated list of RAG evaluation runs with optional filters.

    - **page**: Page number (starts at 1)
    - **page_size**: Number of results per page (max 100)
    - **model**: Filter by specific model name
    - **min_recall**: Filter runs with recall >= this value
    """
    db = SessionLocal()
    try:
        # Build query
        query = db.query(RAGRun)

        # Apply filters
        if model:
            query = query.filter(RAGRun.model_name == model)
        if min_recall is not None:
            query = query.filter(RAGRun.avg_recall >= min_recall)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        runs = query.order_by(desc(RAGRun.timestamp)).offset(offset).limit(page_size).all()

        return RAGRunListResponse(
            total=total,
            page=page,
            page_size=page_size,
            runs=[RAGRunSummary.model_validate(run) for run in runs]
        )

    finally:
        db.close()


@app.get("/rag-run/{run_id}", response_model=RAGRunDetail)
async def get_rag_run_detail(run_id: int):
    """
    Get detailed results for a specific RAG run including all evaluations.

    - **run_id**: Unique identifier for the RAG run

    Returns full RAG run details with per-question breakdown and category analysis.
    """
    run = get_rag_run_by_id(run_id)

    if not run:
        raise HTTPException(status_code=404, detail=f"RAG run {run_id} not found")

    # Calculate category breakdown
    category_breakdown = {}
    for eval in run.evaluations:
        cat = eval.category
        if cat not in category_breakdown:
            category_breakdown[cat] = {
                "total_questions": 0,
                "avg_precision": 0.0,
                "avg_recall": 0.0,
                "avg_f1": 0.0,
                "avg_answer_score": 0.0,
                "avg_grounding_score": 0.0,
                "precisions": [],
                "recalls": [],
                "f1s": [],
                "answer_scores": [],
                "grounding_scores": []
            }
        category_breakdown[cat]["total_questions"] += 1
        category_breakdown[cat]["precisions"].append(eval.retrieval_precision)
        category_breakdown[cat]["recalls"].append(eval.retrieval_recall)
        category_breakdown[cat]["f1s"].append(eval.retrieval_f1)
        category_breakdown[cat]["answer_scores"].append(eval.answer_score)
        category_breakdown[cat]["grounding_scores"].append(eval.grounding_score)

    # Calculate averages
    for cat, data in category_breakdown.items():
        data["avg_precision"] = sum(data["precisions"]) / len(data["precisions"]) if data["precisions"] else 0.0
        data["avg_recall"] = sum(data["recalls"]) / len(data["recalls"]) if data["recalls"] else 0.0
        data["avg_f1"] = sum(data["f1s"]) / len(data["f1s"]) if data["f1s"] else 0.0
        data["avg_answer_score"] = sum(data["answer_scores"]) / len(data["answer_scores"]) if data["answer_scores"] else 0.0
        data["avg_grounding_score"] = sum(data["grounding_scores"]) / len(data["grounding_scores"]) if data["grounding_scores"] else 0.0
        # Remove raw lists from response
        del data["precisions"]
        del data["recalls"]
        del data["f1s"]
        del data["answer_scores"]
        del data["grounding_scores"]

    return RAGRunDetail(
        run=RAGRunSummary.model_validate(run),
        evaluations=[RAGEvaluationDetail.model_validate(e) for e in run.evaluations],
        category_breakdown=category_breakdown
    )


@app.get("/rag-drift/{model_name}", response_model=RAGDriftAnalysis)
async def get_rag_drift(
    model_name: str,
    threshold: float = Query(0.05, ge=0.0, le=1.0, description="Recall drop threshold")
):
    """
    Analyze RAG drift for a specific model.

    Compares latest run to best historical run to detect recall degradation.

    - **model_name**: Name of the model to analyze
    - **threshold**: Recall drop threshold (default 5%)

    Returns drift status and comparison between latest and best runs.
    """
    latest_run, best_run, has_drifted = get_rag_drift_analysis(model_name, threshold)

    if not latest_run:
        raise HTTPException(
            status_code=404,
            detail=f"No RAG evaluation runs found for model: {model_name}"
        )

    recall_drop = (best_run.avg_recall - latest_run.avg_recall) if best_run else 0.0

    return RAGDriftAnalysis(
        model_name=model_name,
        latest_run=RAGRunSummary.model_validate(latest_run) if latest_run else None,
        best_run=RAGRunSummary.model_validate(best_run) if best_run else None,
        has_drifted=has_drifted,
        recall_drop=recall_drop,
        threshold=threshold
    )


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint with basic information."""
    return {
        "name": "Eval Dashboard API",
        "version": "1.0.0",
        "description": "REST API for AI model evaluation tracking and drift detection",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "run_evaluation": "POST /run-evaluation",
            "get_runs": "GET /runs",
            "get_run_detail": "GET /run/{id}",
            "get_models": "GET /models",
            "get_drift": "GET /drift/{model}",
            "get_stats": "GET /stats",
            "test_alerts": "POST /test-alerts/{model}",
            "rag_runs": "GET /rag-runs",
            "rag_run_detail": "GET /rag-run/{id}",
            "rag_drift": "GET /rag-drift/{model}"
        }
    }
