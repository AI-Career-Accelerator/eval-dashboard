"""
Pydantic models for API request/response validation.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


# Request Models
class RunEvaluationRequest(BaseModel):
    """Request to trigger a new evaluation run."""
    models: Optional[List[str]] = Field(
        None,
        description="List of model names to evaluate. If None, evaluates all models."
    )
    webhook_url: Optional[HttpUrl] = Field(
        None,
        description="Callback URL to POST results when evaluation completes."
    )
    max_questions: Optional[int] = Field(
        None,
        description="Limit number of questions to evaluate (for testing)."
    )


# Response Models
class EvaluationDetail(BaseModel):
    """Single question evaluation result."""
    id: int
    question_id: str
    category: str
    question_text: str
    expected_output: str
    model_response: Optional[str]
    judge_score: float
    judge_reasoning: Optional[str]
    latency: Optional[float]
    cost: float

    class Config:
        from_attributes = True


class RunSummary(BaseModel):
    """Summary of a single evaluation run."""
    id: int
    model_name: str
    timestamp: datetime
    commit_hash: Optional[str]
    total_cost: float
    avg_latency: float
    accuracy: float
    total_questions: int
    evaluation_time: float

    class Config:
        from_attributes = True


class RunDetail(BaseModel):
    """Detailed run with all evaluations."""
    run: RunSummary
    evaluations: List[EvaluationDetail]
    category_breakdown: Dict[str, Dict[str, Any]]


class RunListResponse(BaseModel):
    """Paginated list of runs."""
    total: int
    page: int
    page_size: int
    runs: List[RunSummary]


class ModelStats(BaseModel):
    """Statistics for a single model."""
    model_name: str
    total_runs: int
    avg_accuracy: float
    best_accuracy: float
    worst_accuracy: float
    avg_cost: float
    avg_latency: float
    last_run_timestamp: Optional[datetime]


class ModelsResponse(BaseModel):
    """List of available models with their stats."""
    models: List[ModelStats]


class DriftAnalysis(BaseModel):
    """Drift detection results for a model."""
    model_name: str
    latest_run: Optional[RunSummary]
    best_run: Optional[RunSummary]
    has_drifted: bool
    accuracy_drop: float
    threshold: float


class DashboardStats(BaseModel):
    """Overall dashboard statistics."""
    total_runs: int
    total_evaluations: int
    total_models: int
    recent_runs: List[RunSummary]
    top_models: List[ModelStats]


class HealthResponse(BaseModel):
    """API health check response."""
    status: str
    timestamp: datetime
    database_connected: bool
    litellm_proxy_available: bool


class BackgroundTaskResponse(BaseModel):
    """Response when evaluation starts in background."""
    message: str
    job_id: str
    webhook_url: Optional[str]
    models: List[str]
