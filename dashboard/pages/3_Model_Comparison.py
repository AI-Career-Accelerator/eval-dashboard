"""
Model Comparison Page - Compare Performance Across Models
Side-by-side comparison of model metrics with visual heatmap.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_client import get_api_client

# Page config
st.set_page_config(page_title="Model Comparison - Eval Dashboard", page_icon="⚖️", layout="wide")

st.title("⚖️ Model Comparison Matrix")
st.markdown("Compare model performance across accuracy, cost, and latency metrics")
st.divider()

# Get API client
api = get_api_client()

# Fetch model statistics
with st.spinner("Loading model statistics..."):
    models_data = api.get_models()

if not models_data or not models_data.get("models"):
    st.warning("No model data found. Run an evaluation first!")
    st.info("Start an evaluation: `python core/evaluate.py`")
    st.stop()

# Convert to DataFrame
models_df = pd.DataFrame(models_data["models"])

# Filter out models with no runs
models_df = models_df[models_df['total_runs'] > 0]

if models_df.empty:
    st.warning("No completed evaluation runs found.")
    st.stop()

# Sidebar - Filters and Options
st.sidebar.header("Display Options")

# Sort by option
sort_by = st.sidebar.selectbox(
    "Sort By",
    options=['Average Accuracy', 'Best Accuracy', 'Average Cost', 'Average Latency', 'Total Runs'],
    help="Sort models by selected metric"
)

sort_ascending = st.sidebar.checkbox("Ascending Order", value=False)

# Apply sorting
sort_column_map = {
    'Average Accuracy': 'avg_accuracy',
    'Best Accuracy': 'best_accuracy',
    'Average Cost': 'avg_cost',
    'Average Latency': 'avg_latency',
    'Total Runs': 'total_runs'
}

models_df = models_df.sort_values(
    by=sort_column_map[sort_by],
    ascending=sort_ascending
)

# Model selection
st.sidebar.header("Filter Models")
all_models = models_df['model_name'].tolist()
selected_models = st.sidebar.multiselect(
    "Select Models to Compare",
    options=all_models,
    default=all_models[:10] if len(all_models) > 10 else all_models,
    help="Choose models to include in comparison"
)

if not selected_models:
    st.warning("Please select at least one model to compare")
    st.stop()

# Filter DataFrame
filtered_df = models_df[models_df['model_name'].isin(selected_models)].copy()

# Leaderboard Section
st.header("🏆 Model Leaderboard")

# Create display DataFrame
display_df = filtered_df[[
    'model_name',
    'avg_accuracy',
    'best_accuracy',
    'worst_accuracy',
    'avg_cost',
    'avg_latency',
    'total_runs'
]].copy()

# Format columns
display_df['avg_accuracy'] = display_df['avg_accuracy'].apply(lambda x: f"{x:.1%}")
display_df['best_accuracy'] = display_df['best_accuracy'].apply(lambda x: f"{x:.1%}")
display_df['worst_accuracy'] = display_df['worst_accuracy'].apply(lambda x: f"{x:.1%}")
display_df['avg_cost'] = display_df['avg_cost'].apply(lambda x: f"${x:.4f}")
display_df['avg_latency'] = display_df['avg_latency'].apply(lambda x: f"{x:.2f}s")

# Rename columns
display_df = display_df.rename(columns={
    'model_name': 'Model',
    'avg_accuracy': 'Avg Accuracy',
    'best_accuracy': 'Best Accuracy',
    'worst_accuracy': 'Worst Accuracy',
    'avg_cost': 'Avg Cost',
    'avg_latency': 'Avg Latency',
    'total_runs': 'Total Runs'
})

# Add ranking
display_df.insert(0, 'Rank', range(1, len(display_df) + 1))

# Display table with custom styling
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

st.divider()

# Performance Heatmap
st.header("🔥 Performance Heatmap")

# Create heatmap data
heatmap_df = filtered_df[[
    'model_name',
    'avg_accuracy',
    'avg_cost',
    'avg_latency'
]].copy()

# Normalize metrics (0-1 scale for better visualization)
# Higher is better for accuracy, lower is better for cost and latency
heatmap_df['accuracy_norm'] = heatmap_df['avg_accuracy']
heatmap_df['cost_norm'] = 1 - (heatmap_df['avg_cost'] / heatmap_df['avg_cost'].max())
heatmap_df['latency_norm'] = 1 - (heatmap_df['avg_latency'] / heatmap_df['avg_latency'].max())

# Create heatmap
heatmap_data = heatmap_df[['accuracy_norm', 'cost_norm', 'latency_norm']].values
model_names = heatmap_df['model_name'].tolist()
metrics = ['Accuracy', 'Cost\n(lower is better)', 'Latency\n(lower is better)']

fig_heatmap = go.Figure(data=go.Heatmap(
    z=heatmap_data,
    x=metrics,
    y=model_names,
    colorscale='RdYlGn',
    text=[[f"{val:.2f}" for val in row] for row in heatmap_data],
    texttemplate='%{text}',
    textfont={"size": 10},
    colorbar=dict(title="Normalized\nScore")
))

fig_heatmap.update_layout(
    title="Normalized Performance Scores (Green = Better)",
    height=max(400, len(model_names) * 40),
    xaxis_title="Metric",
    yaxis_title="Model"
)

st.plotly_chart(fig_heatmap, use_container_width=True)

st.divider()

# Scatter Plot - Cost vs Accuracy
st.header("💰 Cost-Accuracy Trade-off")

fig_scatter = px.scatter(
    filtered_df,
    x='avg_cost',
    y='avg_accuracy',
    size='avg_latency',
    color='model_name',
    hover_name='model_name',
    hover_data={
        'avg_cost': ':.4f',
        'avg_accuracy': ':.1%',
        'avg_latency': ':.2f',
        'total_runs': True
    },
    title="Model Positioning: Accuracy vs Cost (bubble size = latency)",
    labels={
        'avg_cost': 'Average Cost per Evaluation ($)',
        'avg_accuracy': 'Average Accuracy',
        'avg_latency': 'Avg Latency (s)'
    }
)

fig_scatter.update_layout(
    yaxis_tickformat=".0%",
    height=500,
    showlegend=True
)

# Add quadrant lines
median_cost = filtered_df['avg_cost'].median()
median_accuracy = filtered_df['avg_accuracy'].median()

fig_scatter.add_vline(x=median_cost, line_dash="dash", line_color="gray", opacity=0.5)
fig_scatter.add_hline(y=median_accuracy, line_dash="dash", line_color="gray", opacity=0.5)

st.plotly_chart(fig_scatter, use_container_width=True)

st.caption("💡 **Sweet Spot**: Top-right quadrant = High accuracy + Low cost")

st.divider()

# Detailed Metrics Comparison
st.header("📊 Detailed Metrics")

metrics_tab1, metrics_tab2, metrics_tab3 = st.tabs(["Accuracy", "Cost", "Latency"])

with metrics_tab1:
    # Accuracy comparison
    fig_acc = go.Figure()

    fig_acc.add_trace(go.Bar(
        name='Average',
        x=filtered_df['model_name'],
        y=filtered_df['avg_accuracy'],
        marker_color='lightblue'
    ))

    fig_acc.add_trace(go.Bar(
        name='Best',
        x=filtered_df['model_name'],
        y=filtered_df['best_accuracy'],
        marker_color='green'
    ))

    fig_acc.add_trace(go.Bar(
        name='Worst',
        x=filtered_df['model_name'],
        y=filtered_df['worst_accuracy'],
        marker_color='orange'
    ))

    fig_acc.update_layout(
        title="Accuracy Comparison (Avg, Best, Worst)",
        xaxis_title="Model",
        yaxis_title="Accuracy",
        yaxis_tickformat=".0%",
        barmode='group',
        height=400
    )

    st.plotly_chart(fig_acc, use_container_width=True)

with metrics_tab2:
    # Cost comparison
    fig_cost = px.bar(
        filtered_df,
        x='model_name',
        y='avg_cost',
        title="Average Cost per Evaluation",
        labels={'avg_cost': 'Cost ($)', 'model_name': 'Model'},
        color='avg_cost',
        color_continuous_scale='RdYlGn_r'
    )

    fig_cost.update_layout(height=400)
    st.plotly_chart(fig_cost, use_container_width=True)

with metrics_tab3:
    # Latency comparison
    fig_latency = px.bar(
        filtered_df,
        x='model_name',
        y='avg_latency',
        title="Average Latency per Question",
        labels={'avg_latency': 'Latency (seconds)', 'model_name': 'Model'},
        color='avg_latency',
        color_continuous_scale='RdYlGn_r'
    )

    fig_latency.update_layout(height=400)
    st.plotly_chart(fig_latency, use_container_width=True)

st.divider()

# Winner Cards
st.header("🥇 Category Winners")

col1, col2, col3 = st.columns(3)

with col1:
    best_accuracy_model = filtered_df.loc[filtered_df['avg_accuracy'].idxmax()]
    st.success("**🎯 Most Accurate**")
    st.metric(
        best_accuracy_model['model_name'],
        f"{best_accuracy_model['avg_accuracy']:.1%}"
    )

with col2:
    best_cost_model = filtered_df.loc[filtered_df['avg_cost'].idxmin()]
    st.success("**💰 Most Cost-Effective**")
    st.metric(
        best_cost_model['model_name'],
        f"${best_cost_model['avg_cost']:.4f}"
    )

with col3:
    best_latency_model = filtered_df.loc[filtered_df['avg_latency'].idxmin()]
    st.success("**⚡ Fastest**")
    st.metric(
        best_latency_model['model_name'],
        f"{best_latency_model['avg_latency']:.2f}s"
    )

# Sweet Spot Recommendation
st.divider()
st.header("💡 Recommendation")

# Calculate a composite score (weighted: 50% accuracy, 30% cost, 20% latency)
filtered_df['composite_score'] = (
    0.5 * filtered_df['avg_accuracy'] +
    0.3 * (1 - filtered_df['avg_cost'] / filtered_df['avg_cost'].max()) +
    0.2 * (1 - filtered_df['avg_latency'] / filtered_df['avg_latency'].max())
)

recommended_model = filtered_df.loc[filtered_df['composite_score'].idxmax()]

st.info(
    f"**Recommended Model (Best Overall Balance):** `{recommended_model['model_name']}`\n\n"
    f"- Accuracy: {recommended_model['avg_accuracy']:.1%}\n"
    f"- Cost: ${recommended_model['avg_cost']:.4f}\n"
    f"- Latency: {recommended_model['avg_latency']:.2f}s\n"
    f"- Total Runs: {recommended_model['total_runs']}"
)

st.caption("💡 Tip: Use the sidebar to adjust sorting and filtering options")
