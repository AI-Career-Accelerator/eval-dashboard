"""
Home Page - Accuracy Over Time with Drift Detection
Shows model performance trends and alerts for accuracy degradation.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_client import get_api_client
from utils.theme_manager import apply_theme, render_theme_toggle, get_plotly_template, apply_plot_theme

# Page config
st.set_page_config(page_title="Home - Eval Dashboard", page_icon="📈", layout="wide")

# Apply theme
apply_theme()

st.title("📈 Home - Model Performance Tracker")
st.markdown("Track accuracy trends and catch drift before it impacts production")
st.divider()

# Get API client
api = get_api_client()

# Sidebar filters
st.sidebar.header("Filters")
threshold = st.sidebar.slider(
    "Drift Alert Threshold (%)",
    min_value=1,
    max_value=10,
    value=3,
    help="Alert when accuracy drops by this percentage"
)

# Fetch all runs (API max page_size is 100, so fetch multiple pages if needed)
with st.spinner("Loading evaluation data..."):
    all_runs = []
    page = 1
    while True:
        runs_data = api.get_runs(page=page, page_size=100)
        if not runs_data or not runs_data.get("runs"):
            break
        all_runs.extend(runs_data["runs"])
        if len(runs_data["runs"]) < 100:  # Last page
            break
        page += 1

    runs_data = {"runs": all_runs, "total": len(all_runs)}

if not runs_data or not runs_data.get("runs"):
    st.warning("No evaluation runs found. Run an evaluation first!")
    st.info("Start an evaluation: `python core/evaluate.py`")
    st.stop()

# Convert to DataFrame
runs_df = pd.DataFrame(runs_data["runs"])
runs_df['timestamp'] = pd.to_datetime(runs_df['timestamp'])
runs_df = runs_df.sort_values('timestamp')

# Get unique models
available_models = sorted(runs_df['model_name'].unique())

# Model selector
selected_models = st.sidebar.multiselect(
    "Select Models to Display",
    options=available_models,
    default=available_models[:5] if len(available_models) > 5 else available_models,
    help="Choose which models to show on the chart"
)

# Filter data by selected models
if selected_models:
    filtered_df = runs_df[runs_df['model_name'].isin(selected_models)]
else:
    st.warning("Please select at least one model to display")
    st.stop()

# Drift Analysis Section
st.header("🚨 Drift Detection Alerts")

drift_cols = st.columns(len(selected_models))
drift_threshold = threshold / 100.0  # Convert to decimal

for idx, model in enumerate(selected_models):
    with drift_cols[idx]:
        drift_data = api.get_drift(model, threshold=drift_threshold)

        if drift_data:
            has_drifted = drift_data.get("has_drifted", False)
            accuracy_drop = drift_data.get("accuracy_drop", 0)
            latest_run = drift_data.get("latest_run")
            best_run = drift_data.get("best_run")

            if has_drifted:
                st.error(f"🔴 {model}")
                st.metric(
                    "Accuracy Drop",
                    f"{accuracy_drop:.1%}",
                    delta=f"-{accuracy_drop:.1%}",
                    delta_color="inverse"
                )
                if latest_run and best_run:
                    st.caption(f"Latest: {latest_run['accuracy']:.1%}")
                    st.caption(f"Best: {best_run['accuracy']:.1%}")
            else:
                st.success(f"🟢 {model}")
                if latest_run:
                    st.metric(
                        "Current Accuracy",
                        f"{latest_run['accuracy']:.1%}",
                        delta=f"{accuracy_drop:.1%}" if accuracy_drop < 0 else f"+{abs(accuracy_drop):.1%}"
                    )

st.divider()

# Accuracy Over Time Chart
st.header("📊 Accuracy Trends Over Time")

# Create interactive line chart with Plotly
fig = go.Figure()

for model in selected_models:
    model_data = filtered_df[filtered_df['model_name'] == model]

    fig.add_trace(go.Scatter(
        x=model_data['timestamp'],
        y=model_data['accuracy'],
        mode='lines+markers',
        name=model,
        line=dict(width=2),
        marker=dict(size=8),
        hovertemplate=(
            f"<b>{model}</b><br>" +
            "Accuracy: %{y:.1%}<br>" +
            "Date: %{x|%Y-%m-%d %H:%M}<br>" +
            "<extra></extra>"
        )
    ))

# Add threshold line for reference
if not filtered_df.empty:
    max_accuracy = filtered_df['accuracy'].max()
    threshold_line = max_accuracy * (1 - drift_threshold)

    fig.add_hline(
        y=threshold_line,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Drift Threshold (-{threshold}%)",
        annotation_position="right"
    )

# Update layout
fig.update_layout(
    xaxis_title="Timestamp",
    yaxis_title="Accuracy",
    yaxis_tickformat=".0%",
    hovermode='x unified',
    height=500,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

apply_plot_theme(fig)

st.plotly_chart(fig, use_container_width=True, theme=None)

# Summary Statistics
st.header("📈 Summary Statistics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Runs", len(filtered_df))

with col2:
    best_model = filtered_df.loc[filtered_df['accuracy'].idxmax()]
    st.metric(
        "Best Accuracy",
        f"{best_model['accuracy']:.1%}",
        help=f"{best_model['model_name']} on {best_model['timestamp'].strftime('%Y-%m-%d')}"
    )

with col3:
    avg_accuracy = filtered_df['accuracy'].mean()
    st.metric("Average Accuracy", f"{avg_accuracy:.1%}")

with col4:
    avg_cost = filtered_df['total_cost'].mean()
    st.metric("Average Cost", f"${avg_cost:.3f}")

# Recent Runs Table
st.header("🕒 Recent Evaluation Runs")

# Display table of recent runs
recent_runs = filtered_df.nlargest(10, 'timestamp')[
    ['model_name', 'accuracy', 'avg_latency', 'total_cost', 'timestamp', 'id']
].copy()

recent_runs['timestamp'] = recent_runs['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
recent_runs['accuracy'] = recent_runs['accuracy'].apply(lambda x: f"{x:.1%}")
recent_runs['avg_latency'] = recent_runs['avg_latency'].apply(lambda x: f"{x:.2f}s")
recent_runs['total_cost'] = recent_runs['total_cost'].apply(lambda x: f"${x:.4f}")

recent_runs = recent_runs.rename(columns={
    'model_name': 'Model',
    'accuracy': 'Accuracy',
    'avg_latency': 'Avg Latency',
    'total_cost': 'Total Cost',
    'timestamp': 'Timestamp',
    'id': 'Run ID'
})

st.dataframe(recent_runs, use_container_width=True, hide_index=True)

st.divider()
st.caption("💡 Tip: Click on a model in the legend to hide/show it on the chart")

# Render theme toggle
render_theme_toggle()
