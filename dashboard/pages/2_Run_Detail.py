"""
Run Detail Page - Question-Level Breakdown
Explore individual evaluation runs with detailed results for each question.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_client import get_api_client
from utils.theme_manager import apply_theme, render_theme_toggle, get_plotly_template, apply_plot_theme
from utils.pdf_generator import generate_run_detail_pdf
from datetime import datetime

# Page config
st.set_page_config(page_title="Run Detail - Eval Dashboard", page_icon="🔍", layout="wide")

# Apply theme
apply_theme()

st.title("🔍 Run Detail Explorer")
st.markdown("Drill down into individual evaluation runs and analyze question-level performance")
st.divider()

# Get API client
api = get_api_client()

# Fetch all runs for selection (API max page_size is 100)
with st.spinner("Loading evaluation runs..."):
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

# Create run selector options
runs = runs_data["runs"]
run_options = {
    f"Run #{run['id']} - {run['model_name']} - {run['timestamp'][:19]} ({run['accuracy']:.1%})": run['id']
    for run in runs
}

# Sidebar - Run selector
st.sidebar.header("Select Run")
selected_run_label = st.sidebar.selectbox(
    "Choose an evaluation run",
    options=list(run_options.keys()),
    help="Select a run to view detailed results"
)

selected_run_id = run_options[selected_run_label]

# Fetch detailed run data
with st.spinner("Loading run details..."):
    run_detail = api.get_run_detail(selected_run_id)

if not run_detail:
    st.error("Failed to load run details")
    st.stop()

# Extract data
run_summary = run_detail["run"]
evaluations = run_detail["evaluations"]
category_breakdown = run_detail["category_breakdown"]

# Run Summary Section
st.header("📋 Run Summary")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Model", run_summary["model_name"])

with col2:
    st.metric("Accuracy", f"{run_summary['accuracy']:.1%}")

with col3:
    st.metric("Avg Latency", f"{run_summary['avg_latency']:.2f}s")

with col4:
    st.metric("Total Cost", f"${run_summary['total_cost']:.4f}")

with col5:
    st.metric("Questions", len(evaluations))

# Additional info
with st.expander("ℹ️ Additional Information"):
    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.write(f"**Run ID:** {run_summary['id']}")
        st.write(f"**Timestamp:** {run_summary['timestamp']}")
    with info_col2:
        st.write(f"**Commit Hash:** {run_summary.get('commit_hash', 'N/A')}")
        st.write(f"**Evaluation Time:** {run_summary.get('evaluation_time', 'N/A')}")

st.divider()

# Category Breakdown
st.header("📊 Performance by Category")

if category_breakdown:
    # Convert to DataFrame for visualization
    category_df = pd.DataFrame([
        {
            'Category': cat,
            'Questions': data['total_questions'],
            'Average Score': data['avg_score']
        }
        for cat, data in category_breakdown.items()
    ]).sort_values('Average Score', ascending=False)

    # Create two columns for chart and table
    chart_col, table_col = st.columns([2, 1])

    with chart_col:
        # Bar chart
        fig = px.bar(
            category_df,
            x='Category',
            y='Average Score',
            title='Accuracy by Question Category',
            color='Average Score',
            color_continuous_scale='RdYlGn',
            range_color=[0, 1]
        )
        fig.update_layout(
            yaxis_tickformat=".0%",
            showlegend=False,
            height=400
        )
        apply_plot_theme(fig)
        st.plotly_chart(fig, use_container_width=True, theme=None)

    with table_col:
        # Category stats table
        display_df = category_df.copy()
        display_df['Average Score'] = display_df['Average Score'].apply(lambda x: f"{x:.1%}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

st.divider()

# Question-Level Details
st.header("📝 Question-Level Results")

# Convert evaluations to DataFrame
eval_df = pd.DataFrame(evaluations)

# Sidebar filters for questions
st.sidebar.header("Filter Questions")

# Category filter
categories = sorted(eval_df['category'].unique())
selected_categories = st.sidebar.multiselect(
    "Categories",
    options=categories,
    default=categories,
    help="Filter by question category"
)

# Score filter
min_score = st.sidebar.slider(
    "Minimum Score",
    min_value=0.0,
    max_value=1.0,
    value=0.0,
    step=0.1,
    help="Show only questions with score >= this value"
)

# Filter the dataframe
filtered_eval_df = eval_df[
    (eval_df['category'].isin(selected_categories)) &
    (eval_df['judge_score'] >= min_score)
].copy()

# Sort options
sort_by = st.sidebar.selectbox(
    "Sort By",
    options=['Score (Low to High)', 'Score (High to Low)', 'Latency', 'Cost'],
    help="Sort questions by selected metric"
)

if sort_by == 'Score (Low to High)':
    filtered_eval_df = filtered_eval_df.sort_values('judge_score', ascending=True)
elif sort_by == 'Score (High to Low)':
    filtered_eval_df = filtered_eval_df.sort_values('judge_score', ascending=False)
elif sort_by == 'Latency':
    filtered_eval_df = filtered_eval_df.sort_values('latency', ascending=False)
elif sort_by == 'Cost':
    filtered_eval_df = filtered_eval_df.sort_values('cost', ascending=False)

# Display count
st.caption(f"Showing {len(filtered_eval_df)} of {len(eval_df)} questions")

# Question cards
for idx, row in filtered_eval_df.iterrows():
    # Determine color based on score
    if row['judge_score'] >= 0.8:
        score_color = "🟢"
    elif row['judge_score'] >= 0.5:
        score_color = "🟡"
    else:
        score_color = "🔴"

    with st.expander(
        f"{score_color} Q{row['question_id']} - {row['category']} - Score: {row['judge_score']:.0%}",
        expanded=False
    ):
        # Question details
        detail_col1, detail_col2, detail_col3 = st.columns([2, 1, 1])

        with detail_col1:
            st.markdown("**Question:**")
            st.info(row['question_text'])

        with detail_col2:
            st.metric("Judge Score", f"{row['judge_score']:.0%}")
            st.metric("Latency", f"{row['latency']:.2f}s")

        with detail_col3:
            st.metric("Category", row['category'])
            st.metric("Cost", f"${row['cost']:.5f}")

        # Model response
        st.markdown("**Model Response:**")
        st.success(row['model_response'])

        # Judge reasoning
        if row.get('judge_reasoning'):
            st.markdown("**Judge Reasoning:**")
            st.warning(row['judge_reasoning'])

        # Expected output (if available)
        if row.get('expected_output'):
            st.markdown("**Expected Output:**")
            st.text(row['expected_output'])

st.divider()

# Export option
st.header("💾 Export Results")

export_col1, export_col2 = st.columns(2)

with export_col1:
    # Export to CSV
    csv_data = filtered_eval_df.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv_data,
        file_name=f"run_{selected_run_id}_results.csv",
        mime="text/csv"
    )

with export_col2:
    # Export summary as JSON
    import json
    summary_json = json.dumps({
        "run_summary": run_summary,
        "category_breakdown": category_breakdown,
        "total_questions": len(evaluations)
    }, indent=2)

    st.download_button(
        label="📥 Download Summary as JSON",
        data=summary_json,
        file_name=f"run_{selected_run_id}_summary.json",
        mime="application/json"
    )

st.caption("💡 Tip: Use filters in the sidebar to focus on specific categories or score ranges")

# PDF Export for selected run
st.divider()
st.subheader("📄 Export Run Detail Report")

col1, col2 = st.columns([2, 1])
with col1:
    st.markdown(f"Generate a detailed PDF report for Run #{selected_run_id}")

with col2:
    # Button to trigger PDF generation
    if st.button("📄 Generate PDF", type="primary", use_container_width=True, key="gen_pdf_run"):
        try:
            with st.spinner("Generating PDF report..."):
                pdf_bytes = generate_run_detail_pdf(
                    run_detail['run'],
                    filtered_eval_df,
                    run_detail.get('category_breakdown', {})
                )

            st.success("✅ PDF generated successfully!")

            # Offer download button
            st.download_button(
                label="⬇️ Download Run Detail PDF",
                data=pdf_bytes,
                file_name=f"run_{selected_run_id}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"❌ Failed to generate PDF: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# Render theme toggle
render_theme_toggle()
