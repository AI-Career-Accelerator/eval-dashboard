"""
Eval Dashboard - Main App
Streamlit dashboard for AI model evaluation tracking and drift detection.
"""
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Eval Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">📊 Eval Dashboard</h1>', unsafe_allow_html=True)
st.markdown("**Catch model drift before it kills your product**")
st.divider()

# Main page content
st.header("Welcome to Eval Dashboard")

st.markdown("""
This dashboard provides comprehensive model evaluation tracking and drift detection.

### 📈 Available Pages:

**1. Home** - View accuracy trends over time with drift alerts
**2. Run Detail** - Explore individual evaluation runs with question-level breakdown
**3. Model Comparison** - Compare model performance across metrics
**4. Phoenix Traces** - Visualize LLM execution traces with Phoenix observability

Use the sidebar to navigate between pages.
""")

# API Status Check
st.subheader("🔌 System Status")

import requests

def check_api_status():
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=15)
        if response.status_code == 200:
            data = response.json()
            return True, data
        return False, None
    except:
        return False, None

api_up, health_data = check_api_status()

col1, col2, col3, col4 = st.columns(4)

with col1:
    if api_up:
        st.success("✅ FastAPI Backend: Online")
    else:
        st.error("❌ FastAPI Backend: Offline")
        st.info("Start the API: `python scripts/start_api.py`")

with col2:
    if api_up and health_data:
        if health_data.get("database_connected"):
            st.success("✅ Database: Connected")
        else:
            st.error("❌ Database: Disconnected")
            st.caption("Restart the API to reconnect")
    else:
        st.warning("⚠️ Database: Unknown")

with col3:
    if api_up and health_data:
        if health_data.get("litellm_proxy_available"):
            st.success("✅ LiteLLM Proxy: Available")
        else:
            st.info("ℹ️ LiteLLM Proxy: Unavailable")
            st.caption("Only needed for new evaluations")
    else:
        st.warning("⚠️ LiteLLM: Unknown")

with col4:
    # Check Phoenix status
    try:
        phoenix_response = requests.get("http://localhost:6006", timeout=2)
        if phoenix_response.status_code == 200:
            st.success("✅ Phoenix: Online")
            st.caption("[View Traces](http://localhost:6006)")
        else:
            st.info("ℹ️ Phoenix: Offline")
            st.caption("Auto-starts with evaluations")
    except:
        st.info("ℹ️ Phoenix: Offline")
        st.caption("Auto-starts with evaluations")

# Quick stats preview
if api_up:
    st.subheader("📊 Quick Stats")
    try:
        stats_response = requests.get("http://127.0.0.1:8000/stats", timeout=5)
        if stats_response.status_code == 200:
            stats = stats_response.json()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Runs", stats.get("total_runs", 0))
            with col2:
                st.metric("Total Evaluations", stats.get("total_evaluations", 0))
            with col3:
                st.metric("Models Evaluated", stats.get("total_models", 0))
            with col4:
                if stats.get("top_models"):
                    best_model = stats["top_models"][0]
                    st.metric(
                        "Best Model",
                        best_model.get("model_name", "N/A"),
                        f"{best_model.get('avg_accuracy', 0):.1%}"
                    )
    except Exception as e:
        st.warning(f"Could not fetch stats: {str(e)}")

st.divider()
st.caption("Built in Public - Day 8/14 | Now with Phoenix Observability!")
