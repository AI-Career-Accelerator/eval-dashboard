"""
RAG Analysis Page - Retrieval Quality & Grounding Metrics
Shows RAG-specific performance: retrieval precision/recall, grounding scores, and drift detection.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_client import get_api_client

# Page config
st.set_page_config(page_title="RAG Analysis - Eval Dashboard", page_icon="🔍", layout="wide")

st.title("🔍 RAG Analysis - Retrieval Quality Tracker")
st.markdown("Monitor retrieval precision/recall, answer grounding, and RAG-specific drift")
st.divider()

# Get API client
api = get_api_client()

# Sidebar filters
st.sidebar.header("Filters")
recall_threshold_slider = st.sidebar.slider(
    "Min Recall Threshold (%)",
    min_value=0,
    max_value=100,
    value=70,
    help="Show only runs with recall above this threshold"
)

drift_threshold = st.sidebar.slider(
    "Drift Alert Threshold (%)",
    min_value=1,
    max_value=10,
    value=5,
    help="Alert when recall drops by this percentage"
)

# Fetch all RAG runs
with st.spinner("Loading RAG evaluation data..."):
    all_rag_runs = []
    page = 1
    while True:
        rag_runs_data = api.get_rag_runs(page=page, page_size=100)
        if not rag_runs_data or not rag_runs_data.get("runs"):
            break
        all_rag_runs.extend(rag_runs_data["runs"])
        if len(rag_runs_data["runs"]) < 100:  # Last page
            break
        page += 1

    rag_runs_data = {"runs": all_rag_runs, "total": len(all_rag_runs)}

if not rag_runs_data or not rag_runs_data.get("runs"):
    st.warning("No RAG evaluation runs found. Run a RAG evaluation first!")
    st.info("Start a RAG evaluation: `python core/rag_evaluate.py`")
    st.code("""
# Quick test (first 10 questions)
cd core
python rag_evaluate.py
    """, language="bash")
    st.stop()

# Convert to DataFrame
rag_runs_df = pd.DataFrame(rag_runs_data["runs"])
rag_runs_df['timestamp'] = pd.to_datetime(rag_runs_df['timestamp'])
rag_runs_df = rag_runs_df.sort_values('timestamp')

# Get unique models
available_models = sorted(rag_runs_df['model_name'].unique())

# Model selector
selected_models = st.sidebar.multiselect(
    "Select Models to Display",
    options=available_models,
    default=available_models[:3] if len(available_models) > 3 else available_models,
    help="Choose which models to show on the charts"
)

# Filter data by selected models and recall threshold
if selected_models:
    filtered_df = rag_runs_df[rag_runs_df['model_name'].isin(selected_models)]
    min_recall = recall_threshold_slider / 100.0
    if min_recall > 0:
        filtered_df = filtered_df[filtered_df['avg_recall'] >= min_recall]
else:
    st.warning("Please select at least one model to display")
    st.stop()

# ============================================================================
# RAG DRIFT DETECTION ALERTS
# ============================================================================

st.header("🚨 RAG Drift Detection Alerts")

drift_cols = st.columns(len(selected_models))
drift_threshold_decimal = drift_threshold / 100.0  # Convert to decimal

for idx, model in enumerate(selected_models):
    with drift_cols[idx]:
        drift_data = api.get_rag_drift(model, threshold=drift_threshold_decimal)

        if drift_data:
            has_drifted = drift_data.get("has_drifted", False)
            recall_drop = drift_data.get("recall_drop", 0)
            latest_run = drift_data.get("latest_run")
            best_run = drift_data.get("best_run")

            if has_drifted:
                st.error(f"🔴 {model}")
                st.metric(
                    "Recall Drop",
                    f"{recall_drop:.1%}",
                    delta=f"-{recall_drop:.1%}",
                    delta_color="inverse"
                )
            else:
                st.success(f"✅ {model}")
                st.metric(
                    "Recall Drop",
                    f"{recall_drop:.1%}",
                    delta=f"{recall_drop:.1%}" if recall_drop >= 0 else f"-{abs(recall_drop):.1%}",
                    delta_color="normal"
                )

            if latest_run and best_run:
                st.caption(f"Latest: {latest_run['avg_recall']:.1%} | Best: {best_run['avg_recall']:.1%}")

st.divider()

# ============================================================================
# KEY METRICS OVERVIEW
# ============================================================================

st.header("📊 Key Metrics Overview")

# Calculate aggregate stats
latest_runs_per_model = filtered_df.groupby('model_name').last()

col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_precision = filtered_df['avg_precision'].mean()
    st.metric("Avg Precision@K", f"{avg_precision:.1%}")

with col2:
    avg_recall = filtered_df['avg_recall'].mean()
    st.metric("Avg Recall@K", f"{avg_recall:.1%}")

with col3:
    avg_answer_score = filtered_df['avg_answer_score'].mean()
    st.metric("Avg Answer Score", f"{avg_answer_score:.1%}")

with col4:
    avg_grounding = filtered_df['avg_grounding_score'].mean()
    st.metric("Avg Grounding Score", f"{avg_grounding:.1%}")

st.divider()

# ============================================================================
# RETRIEVAL QUALITY OVER TIME
# ============================================================================

st.header("📈 Retrieval Quality Over Time")

tab1, tab2, tab3 = st.tabs(["Precision & Recall", "Answer Quality", "Performance"])

with tab1:
    fig = go.Figure()

    for model in selected_models:
        model_data = filtered_df[filtered_df['model_name'] == model]

        # Precision line
        fig.add_trace(go.Scatter(
            x=model_data['timestamp'],
            y=model_data['avg_precision'],
            name=f"{model} - Precision",
            mode='lines+markers',
            line=dict(dash='dot')
        ))

        # Recall line
        fig.add_trace(go.Scatter(
            x=model_data['timestamp'],
            y=model_data['avg_recall'],
            name=f"{model} - Recall",
            mode='lines+markers',
            line=dict(dash='solid')
        ))

    fig.update_layout(
        title="Precision@K and Recall@K Over Time",
        xaxis_title="Timestamp",
        yaxis_title="Score (0-1)",
        hovermode='x unified',
        yaxis=dict(range=[0, 1]),
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption("""
    **Precision@K**: Percentage of retrieved chunks that are relevant
    **Recall@K**: Percentage of all relevant chunks that were retrieved
    💡 High recall = Not missing important info | High precision = Low noise
    """)

with tab2:
    fig2 = go.Figure()

    for model in selected_models:
        model_data = filtered_df[filtered_df['model_name'] == model]

        # Answer score line
        fig2.add_trace(go.Scatter(
            x=model_data['timestamp'],
            y=model_data['avg_answer_score'],
            name=f"{model} - Answer",
            mode='lines+markers'
        ))

        # Grounding score line
        fig2.add_trace(go.Scatter(
            x=model_data['timestamp'],
            y=model_data['avg_grounding_score'],
            name=f"{model} - Grounding",
            mode='lines+markers',
            line=dict(dash='dash')
        ))

    fig2.update_layout(
        title="Answer Correctness & Grounding Over Time",
        xaxis_title="Timestamp",
        yaxis_title="Score (0-1)",
        hovermode='x unified',
        yaxis=dict(range=[0, 1]),
        height=500
    )

    st.plotly_chart(fig2, use_container_width=True)

    st.caption("""
    **Answer Score**: How correct the final answer is
    **Grounding Score**: How well the answer cites the provided context
    💡 High answer + Low grounding = Hallucination risk!
    """)

with tab3:
    fig3 = go.Figure()

    for model in selected_models:
        model_data = filtered_df[filtered_df['model_name'] == model]

        # Retrieval time
        fig3.add_trace(go.Scatter(
            x=model_data['timestamp'],
            y=model_data['avg_retrieval_time'],
            name=f"{model} - Retrieval",
            mode='lines+markers'
        ))

        # Generation time
        fig3.add_trace(go.Scatter(
            x=model_data['timestamp'],
            y=model_data['avg_generation_time'],
            name=f"{model} - Generation",
            mode='lines+markers',
            line=dict(dash='dash')
        ))

    fig3.update_layout(
        title="Latency Breakdown: Retrieval vs Generation",
        xaxis_title="Timestamp",
        yaxis_title="Time (seconds)",
        hovermode='x unified',
        height=500
    )

    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ============================================================================
# MODEL COMPARISON MATRIX
# ============================================================================

st.header("🔬 Model Comparison Matrix")

# Get latest run for each model
comparison_data = []
for model in selected_models:
    model_data = filtered_df[filtered_df['model_name'] == model]
    if not model_data.empty:
        latest = model_data.iloc[-1]
        comparison_data.append({
            'Model': model,
            'Precision@K': f"{latest['avg_precision']:.2%}",
            'Recall@K': f"{latest['avg_recall']:.2%}",
            'F1@K': f"{latest['avg_f1']:.2%}",
            'MRR': f"{latest['avg_mrr']:.3f}",
            'Answer Score': f"{latest['avg_answer_score']:.2%}",
            'Grounding': f"{latest['avg_grounding_score']:.2%}",
            'Retrieval Time': f"{latest['avg_retrieval_time']:.2f}s",
            'Total Cost': f"${latest['total_cost']:.4f}",
            'Questions': latest['total_questions']
        })

comparison_df = pd.DataFrame(comparison_data)
st.dataframe(comparison_df, use_container_width=True, hide_index=True)

st.divider()

# ============================================================================
# RUN HISTORY TABLE
# ============================================================================

st.header("📜 Recent RAG Evaluation Runs")

# Prepare display dataframe
display_df = filtered_df[['id', 'model_name', 'timestamp', 'avg_precision', 'avg_recall',
                           'avg_f1', 'avg_answer_score', 'avg_grounding_score',
                           'total_cost', 'total_questions']].copy()

display_df = display_df.rename(columns={
    'id': 'Run ID',
    'model_name': 'Model',
    'timestamp': 'Timestamp',
    'avg_precision': 'Precision',
    'avg_recall': 'Recall',
    'avg_f1': 'F1',
    'avg_answer_score': 'Answer Score',
    'avg_grounding_score': 'Grounding',
    'total_cost': 'Cost',
    'total_questions': 'Questions'
})

# Format percentages and costs
display_df['Precision'] = display_df['Precision'].apply(lambda x: f"{x:.1%}")
display_df['Recall'] = display_df['Recall'].apply(lambda x: f"{x:.1%}")
display_df['F1'] = display_df['F1'].apply(lambda x: f"{x:.1%}")
display_df['Answer Score'] = display_df['Answer Score'].apply(lambda x: f"{x:.1%}")
display_df['Grounding'] = display_df['Grounding'].apply(lambda x: f"{x:.1%}")
display_df['Cost'] = display_df['Cost'].apply(lambda x: f"${x:.4f}")

# Sort by timestamp descending
display_df = display_df.sort_values('Timestamp', ascending=False)

st.dataframe(display_df, use_container_width=True, hide_index=True)

# ============================================================================
# DIAGNOSTICS SECTION
# ============================================================================

st.divider()
st.header("🔧 Diagnostic Insights")

st.markdown("""
### How to Read RAG Metrics

**Retrieval Metrics:**
- **Precision@K**: What % of retrieved chunks are actually relevant? (Quality)
- **Recall@K**: Did we find all the relevant chunks? (Coverage)
- **MRR**: Is the most relevant chunk ranked first?

**Answer Metrics:**
- **Answer Score**: Is the final answer factually correct?
- **Grounding Score**: Does the answer use the provided context, or is it hallucinating?

**Common Issues:**

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Low Recall + Low Answer Score | **Vector search failing** | Reindex embeddings, try different embedding model |
| High Recall + Low Answer Score | **LLM can't use context** | Improve prompt, use stronger model |
| High Recall + High Answer + Low Grounding | **Hallucination risk** | Model has memorized answers, not using context |
| High Precision + Low Recall | **Too conservative retrieval** | Increase Top-K parameter |

**Next Steps:**
1. Click on a specific Run ID to see question-level breakdown
2. Use drift alerts to catch degradation early
3. Compare different retrieval-K values to optimize quality vs speed
""")

# Footer
st.divider()
st.caption("RAG Analysis Dashboard | Powered by FastAPI + Streamlit | Data updates in real-time")
