"""
API Client for FastAPI Backend
Handles all HTTP communication with the evaluation API.
"""
import requests
from typing import Optional, List, Dict, Any
import streamlit as st

# Base URL for the FastAPI backend
BASE_URL = "http://127.0.0.1:8000"


class APIClient:
    """Client for interacting with the Eval Dashboard API."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Make a GET request to the API."""
        try:
            response = self.session.get(
                f"{self.base_url}{endpoint}",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def _post(self, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Make a POST request to the API."""
        try:
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    # Health check
    def get_health(self) -> Optional[Dict[str, Any]]:
        """Check API health status."""
        return self._get("/health")

    # Stats endpoints
    def get_stats(self) -> Optional[Dict[str, Any]]:
        """Get overall dashboard statistics."""
        return self._get("/stats")

    # Runs endpoints
    def get_runs(
        self,
        page: int = 1,
        page_size: int = 20,
        model: Optional[str] = None,
        min_accuracy: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get paginated list of evaluation runs.

        Args:
            page: Page number (starts at 1)
            page_size: Items per page
            model: Filter by model name
            min_accuracy: Filter by minimum accuracy

        Returns:
            Dict with 'total', 'page', 'page_size', and 'runs' list
        """
        params = {
            "page": page,
            "page_size": page_size
        }
        if model:
            params["model"] = model
        if min_accuracy is not None:
            params["min_accuracy"] = min_accuracy

        return self._get("/runs", params=params)

    def get_run_detail(self, run_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed results for a specific run.

        Args:
            run_id: Unique identifier for the run

        Returns:
            Dict with 'run', 'evaluations', and 'category_breakdown'
        """
        return self._get(f"/run/{run_id}")

    # Models endpoints
    def get_models(self) -> Optional[Dict[str, Any]]:
        """
        Get statistics for all available models.

        Returns:
            Dict with 'models' list containing ModelStats for each model
        """
        return self._get("/models")

    # Drift endpoints
    def get_drift(self, model_name: str, threshold: float = 0.05) -> Optional[Dict[str, Any]]:
        """
        Analyze drift for a specific model.

        Args:
            model_name: Name of the model to analyze
            threshold: Accuracy drop threshold (default 5%)

        Returns:
            Dict with drift analysis including latest_run, best_run, has_drifted, accuracy_drop
        """
        params = {"threshold": threshold}
        return self._get(f"/drift/{model_name}", params=params)

    # Evaluation trigger
    def run_evaluation(
        self,
        models: Optional[List[str]] = None,
        webhook_url: Optional[str] = None,
        max_questions: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Trigger a new evaluation run in the background.

        Args:
            models: List of models to evaluate
            webhook_url: Optional callback URL
            max_questions: Optional limit on questions

        Returns:
            Dict with job_id and task info
        """
        data = {}
        if models:
            data["models"] = models
        if webhook_url:
            data["webhook_url"] = webhook_url
        if max_questions:
            data["max_questions"] = max_questions

        return self._post("/run-evaluation", data=data)


# Singleton instance
@st.cache_resource
def get_api_client() -> APIClient:
    """Get cached API client instance."""
    return APIClient()
