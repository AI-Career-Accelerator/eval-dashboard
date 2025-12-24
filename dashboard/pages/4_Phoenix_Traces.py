"""
Phoenix Traces Page
Visualize LLM execution traces with Arize Phoenix observability.
"""
import streamlit as st
import requests
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.theme_manager import apply_theme, render_theme_toggle

st.set_page_config(
    page_title="Phoenix Traces",
    page_icon="🔍",
    layout="wide"
)

# Apply theme
apply_theme()

st.title("🔍 Phoenix Observability")
st.markdown("**Visualize LLM execution traces with waterfall timelines**")
st.divider()

# Check Phoenix status
def check_phoenix_status():
    try:
        response = requests.get("http://localhost:6006", timeout=2)
        return response.status_code == 200
    except:
        return False

phoenix_online = check_phoenix_status()

# Phoenix Status Banner
if phoenix_online:
    st.success("✅ Phoenix is running at http://localhost:6006")

    # Create tabs for different trace views
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔗 Direct Access", "ℹ️ About"])

    with tab1:
        st.subheader("Phoenix Dashboard (Embedded)")
        st.markdown("""
        The Phoenix UI provides:
        - **Trace Waterfall**: See execution flow with latency breakdown
        - **Span Details**: Inspect individual LLM calls, prompts, and responses
        - **Performance Metrics**: Track token usage, costs, and latency
        - **Search & Filter**: Find specific traces by model, time, or content
        """)

        st.info("📌 **Tip:** Phoenix traces are automatically captured when you run evaluations with `python core/evaluate.py`")

        # Embed Phoenix UI in iframe
        st.components.v1.iframe("http://localhost:6006", height=800, scrolling=True)

    with tab2:
        st.subheader("Direct Phoenix Access")
        st.markdown(f"Open Phoenix in a new tab for the full experience:")
        st.link_button("🚀 Open Phoenix UI", "http://localhost:6006", type="primary")

        st.divider()

        st.markdown("### 🎯 What to Look For in Traces")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **Performance Insights:**
            - Total request latency
            - Time spent in model inference
            - Network overhead
            - Judge evaluation time
            """)

        with col2:
            st.markdown("""
            **Debugging Information:**
            - Exact prompts sent to models
            - Complete model responses
            - Token counts and costs
            - Error messages and retries
            """)

        st.divider()

        st.markdown("### 📸 Example Trace View")
        st.markdown("""
        A typical Phoenix trace shows:

        1. **Span Waterfall** - Visual timeline of all operations
        2. **Model Call Details** - Input/output for each LLM request
        3. **Attributes** - Metadata like model name, tokens, temperature
        4. **Events** - Streaming chunks, retries, errors
        """)

    with tab3:
        st.subheader("About Phoenix Integration")

        st.markdown("""
        ### 🦅 Arize Phoenix

        Phoenix is an open-source observability platform designed specifically for LLM applications.

        **Key Features:**
        - **OpenTelemetry-based**: Industry-standard instrumentation
        - **Auto-instrumentation**: Captures traces without code changes
        - **Multi-framework**: Works with OpenAI, LangChain, LlamaIndex, and more
        - **Local-first**: Runs on your machine, no cloud required

        **How it Works in This Dashboard:**
        1. Phoenix server launches automatically when running evaluations
        2. OpenInference instrumentation captures all OpenAI SDK calls
        3. Traces are sent to Phoenix via OTLP (OpenTelemetry Protocol)
        4. You can view and analyze traces in the Phoenix UI

        **Resources:**
        - [Phoenix Documentation](https://docs.arize.com/phoenix)
        - [OpenInference Spec](https://github.com/Arize-ai/openinference)
        - [GitHub Repository](https://github.com/Arize-ai/phoenix)
        """)

        st.divider()

        st.markdown("### 🔄 Phoenix vs LangSmith")

        comparison_data = {
            "Feature": ["Open Source", "Self-Hosted", "Auto-Instrumentation", "Waterfall Traces", "Cost", "Setup"],
            "Phoenix": ["✅ Yes", "✅ Local", "✅ Yes", "✅ Yes", "Free", "~5 min"],
            "LangSmith": ["❌ No", "☁️ Cloud", "✅ Yes", "✅ Yes", "Paid", "~10 min"]
        }

        st.table(comparison_data)

        st.info("💡 **Pro Tip:** This dashboard will eventually support both Phoenix AND LangSmith for side-by-side comparison!")

else:
    st.error("❌ Phoenix is not running")
    st.markdown("""
    ### How to Start Phoenix

    Phoenix will automatically start when you run evaluations:

    ```bash
    # Run an evaluation (Phoenix starts automatically)
    python core/evaluate.py
    ```

    **Or start Phoenix manually:**

    ```python
    import phoenix as px
    px.launch_app()  # Opens at http://localhost:6006
    ```

    **Check if Phoenix is running:**
    ```bash
    curl http://localhost:6006
    ```
    """)

    st.divider()

    st.info("📚 Learn more at [Phoenix Documentation](https://docs.arize.com/phoenix)")

# Footer
st.divider()
st.caption(f"Built in Public - Day 11/14 | Dashboard Polish + Dark Mode!")

# Render theme toggle
render_theme_toggle()
