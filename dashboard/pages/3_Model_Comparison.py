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
import urllib.parse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_client import get_api_client
from utils.theme_manager import apply_theme, render_theme_toggle, get_plotly_template, apply_plot_theme
from utils.pdf_generator import generate_model_comparison_pdf
from datetime import datetime

# Page config
st.set_page_config(page_title="Model Comparison - Eval Dashboard", page_icon="⚖️", layout="wide")

# Apply theme
apply_theme()

st.title("⚖️ Model Comparison Matrix")
st.markdown("Compare model performance across accuracy, cost, and latency metrics")
st.divider()

# Get API client
api = get_api_client()

# Sidebar - Time Filter (needs to be defined BEFORE API call)
st.sidebar.header("🕐 Time Period")

# Time filter
time_filter_options = {
    "All Time": None,
    "Last 7 Days": 7,
    "Last 30 Days": 30
}

time_filter = st.sidebar.selectbox(
    "Show results from",
    options=list(time_filter_options.keys()),
    index=0,
    help="Filter model statistics by time period"
)

selected_days = time_filter_options[time_filter]

# Fetch model statistics with time filter
with st.spinner("Loading model statistics..."):
    models_data = api.get_models(days=selected_days)

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

# Sidebar - Display Options
st.sidebar.divider()
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

# Show time period badge
if time_filter == "Last 7 Days":
    st.caption("📅 **Weekly Leaderboard** - Rankings from the past 7 days")
elif time_filter == "Last 30 Days":
    st.caption("📅 **Monthly Leaderboard** - Rankings from the past 30 days")
else:
    st.caption("📅 **All-Time Leaderboard** - Complete historical rankings")

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

# Add ranking with medals for top 3
ranks = []
for i in range(1, len(display_df) + 1):
    if i == 1:
        ranks.append("🥇 1")
    elif i == 2:
        ranks.append("🥈 2")
    elif i == 3:
        ranks.append("🥉 3")
    else:
        ranks.append(str(i))

display_df.insert(0, 'Rank', ranks)

# Highlight the champion
if not filtered_df.empty:
    champion = filtered_df.iloc[0]
    champion_name = champion['model_name']
    champion_accuracy = champion['avg_accuracy']
    champion_cost = champion['avg_cost']
    champion_latency = champion['avg_latency']

    # Champion card
    period_label = "Weekly" if time_filter == "Last 7 Days" else ("Monthly" if time_filter == "Last 30 Days" else "All-Time")
    st.success(f"**🏆 {period_label} Champion: {champion_name}**")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Accuracy", f"{champion_accuracy:.1%}")
    with col2:
        st.metric("Avg Cost", f"${champion_cost:.4f}")
    with col3:
        st.metric("Avg Latency", f"{champion_latency:.2f}s")
    with col4:
        # Shareable tweet button
        tweet_text = f"🏆 {period_label} AI Model Champion: {champion_name}\n\n✅ Accuracy: {champion_accuracy:.1%}\n💰 Cost: ${champion_cost:.4f}\n⚡ Latency: {champion_latency:.2f}s\n\nTracked with my eval dashboard 📊"
        tweet_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(tweet_text)}"
        st.markdown(f"[🐦 Share on Twitter]({tweet_url})", unsafe_allow_html=True)

st.divider()

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

apply_plot_theme(fig_heatmap)

st.plotly_chart(fig_heatmap, use_container_width=True, theme=None)

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
apply_plot_theme(fig_scatter)
st.plotly_chart(fig_scatter, use_container_width=True, theme=None)

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
    
    apply_plot_theme(fig_acc)

    st.plotly_chart(fig_acc, use_container_width=True, theme=None)

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
    apply_plot_theme(fig_cost)
    st.plotly_chart(fig_cost, use_container_width=True, theme=None)

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
    apply_plot_theme(fig_latency)
    st.plotly_chart(fig_latency, use_container_width=True, theme=None)

st.divider()

# Cost Savings Calculator
st.header("💰 Cost Savings Calculator")
st.markdown("**Calculate potential savings by choosing the optimal model vs GPT-4o baseline**")

# Find GPT-4o baseline (or closest match)
gpt4o_baseline = filtered_df[filtered_df['model_name'].str.contains('gpt-4o', case=False, na=False)]
if not gpt4o_baseline.empty:
    baseline_cost = gpt4o_baseline.iloc[0]['avg_cost']
    baseline_model = gpt4o_baseline.iloc[0]['model_name']
else:
    # Fallback: use the most expensive model as baseline
    baseline_cost = filtered_df['avg_cost'].max()
    baseline_model = filtered_df.loc[filtered_df['avg_cost'].idxmax(), 'model_name']

st.caption(f"Using **{baseline_model}** as baseline (${baseline_cost:.4f} per evaluation)")

# Usage projections
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 Usage Projections")

    # User inputs for projections
    evals_per_day = st.slider(
        "Evaluations per day",
        min_value=10,
        max_value=10000,
        value=100,
        step=10,
        help="Estimated number of model evaluations per day in production"
    )

    selected_model_for_calc = st.selectbox(
        "Compare model",
        options=selected_models,
        index=0,
        help="Model to compare against baseline"
    )

with col2:
    st.subheader("💸 Projected Savings")

    # Calculate savings
    selected_model_cost = filtered_df[filtered_df['model_name'] == selected_model_for_calc].iloc[0]['avg_cost']
    cost_diff_per_eval = baseline_cost - selected_model_cost

    # Calculate projections
    daily_savings = cost_diff_per_eval * evals_per_day
    weekly_savings = daily_savings * 7
    monthly_savings = daily_savings * 30
    annual_savings = daily_savings * 365

    # Display metrics
    metric_cols = st.columns(4)

    with metric_cols[0]:
        st.metric(
            "Daily Savings",
            f"${abs(daily_savings):.2f}",
            delta=f"${cost_diff_per_eval:.4f} per eval",
            delta_color="normal" if daily_savings >= 0 else "inverse"
        )

    with metric_cols[1]:
        st.metric(
            "Weekly Savings",
            f"${abs(weekly_savings):.2f}",
            delta=None
        )

    with metric_cols[2]:
        st.metric(
            "Monthly Savings",
            f"${abs(monthly_savings):.2f}",
            delta=None
        )

    with metric_cols[3]:
        st.metric(
            "Annual Savings",
            f"${abs(annual_savings):,.2f}",
            delta=None
        )

    # Summary message
    if daily_savings > 0:
        st.success(
            f"✅ **Switching to {selected_model_for_calc} saves ${monthly_savings:.2f}/month** "
            f"(${annual_savings:,.2f}/year) at {evals_per_day} evals/day"
        )

        # ROI comparison
        accuracy_diff = (
            filtered_df[filtered_df['model_name'] == selected_model_for_calc].iloc[0]['avg_accuracy'] -
            filtered_df[filtered_df['model_name'] == baseline_model].iloc[0]['avg_accuracy']
        )

        if accuracy_diff >= 0:
            st.info(
                f"🎯 **Bonus:** {selected_model_for_calc} is also "
                f"{abs(accuracy_diff):.1%} {'more' if accuracy_diff > 0 else 'equally'} accurate!"
            )
        else:
            st.warning(
                f"⚠️ **Trade-off:** {selected_model_for_calc} is "
                f"{abs(accuracy_diff):.1%} less accurate. Evaluate if acceptable for your use case."
            )
    elif daily_savings < 0:
        st.error(
            f"❌ {selected_model_for_calc} costs ${abs(monthly_savings):.2f}/month MORE than {baseline_model}"
        )
    else:
        st.info(f"ℹ️ Both models have identical costs")

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

# PDF Export - Generate and offer download
st.divider()
st.subheader("📄 Export Executive Report")

col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("Generate a professional PDF report with charts, tables, and recommendations.")

with col2:
    # Button to trigger PDF generation
    if st.button("📄 Generate PDF", type="primary", use_container_width=True):
        try:
            with st.spinner("Generating PDF report..."):
                pdf_bytes = generate_model_comparison_pdf(filtered_df)

            st.success("✅ PDF generated successfully!")

            # Offer download button
            st.download_button(
                label="⬇️ Download PDF Report",
                data=pdf_bytes,
                file_name=f"model_comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"❌ Failed to generate PDF: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# Render theme toggle
render_theme_toggle()
