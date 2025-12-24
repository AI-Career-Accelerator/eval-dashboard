"""
Theme Manager - Dark/Light Mode Toggle
Provides dynamic theme switching via CSS injection.
"""
import streamlit as st


def get_dark_mode_css() -> str:
    """Return CSS for dark mode styling."""
    return """
    <style>
    /* Dark mode styles */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }

    .main-header {
        color: #58a6ff !important;
    }

    .metric-card {
        background-color: #1c1f26 !important;
        border: 1px solid #30363d;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b22;
    }

    [data-testid="stSidebar"] * {
        color: #c9d1d9 !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #fafafa;
    }

    [data-testid="stMetricLabel"] {
        color: #8b949e;
    }

    /* Dataframes and Tables - INVERT STRATEGY */
    /* Since base theme is Light, st.dataframe renders white. We invert it to make it dark. */
    [data-testid="stDataFrame"] {
        filter: invert(1) hue-rotate(180deg);
    }

    /* Table cells (for static st.table) */
    table {
        background-color: #0d1117 !important;
        color: #c9d1d9 !important;
    }

    th {
        background-color: #161b22 !important;
        color: #58a6ff !important;
    }

    td {
        background-color: #0d1117 !important;
        color: #c9d1d9 !important;
    }

    /* Plotly charts dark background */
    .js-plotly-plot {
        background-color: #0d1117 !important;
    }

    .plotly {
        background-color: #0d1117 !important;
    }

    .main .block-container {
        background-color: #0e1117 !important;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #fafafa !important;
    }

    /* Dividers */
    hr {
        border-color: #30363d;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #161b22 !important;
    }

    .stTabs [data-baseweb="tab"] {
        color: #8b949e !important;
        background-color: transparent !important;
    }

    .stTabs [aria-selected="true"] {
        color: #58a6ff !important;
        background-color: #0d1117 !important;
    }

    /* Tab content panels */
    [data-baseweb="tab-panel"] {
        background-color: #0d1117 !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
    }

    .stButton > button:hover {
        background-color: #30363d;
        border-color: #58a6ff;
    }

    /* Text inputs */
    .stTextInput > div > div > input {
        background-color: #0d1117;
        color: #c9d1d9;
        border-color: #30363d;
    }

    /* Select boxes */
    .stSelectbox > div > div {
        background-color: #0d1117;
        color: #c9d1d9;
    }

    /* Number inputs */
    .stNumberInput > div > div > input {
        background-color: #0d1117 !important;
        color: #c9d1d9 !important;
        border-color: #30363d !important;
    }

    /* Select boxes */
    .stSelectbox > div > div {
        background-color: #0d1117 !important;
        color: #c9d1d9 !important;
    }

    [data-baseweb="select"] {
        background-color: #0d1117 !important;
    }

    [data-baseweb="select"] > div {
        background-color: #0d1117 !important;
        border-color: #30363d !important;
        color: #c9d1d9 !important;
    }

    /* Sliders */
    .stSlider > div > div > div {
        background-color: #30363d !important;
    }

    .stSlider [role="slider"] {
        background-color: #58a6ff !important;
    }

    /* Dropdown menus */
    [role="listbox"] {
        background-color: #161b22 !important;
        border-color: #30363d !important;
    }

    [role="option"] {
        background-color: #161b22 !important;
        color: #c9d1d9 !important;
    }

    [role="option"]:hover {
        background-color: #21262d !important;
    }

    /* Success/Error/Warning/Info boxes */
    .stSuccess {
        background-color: #033a16;
        border-color: #2ea043;
    }

    .stError {
        background-color: #490202;
        border-color: #f85149;
    }

    .stWarning {
        background-color: #4d2800;
        border-color: #f0883e;
    }

    .stInfo {
        background-color: #051d4d;
        border-color: #58a6ff;
    }

    /* Captions */
    .caption {
        color: #8b949e !important;
    }

    /* Markdown links */
    a {
        color: #58a6ff !important;
    }

    a:hover {
        color: #79c0ff !important;
    }

    /* Expanders */
    [data-testid="stExpander"] {
        background-color: #161b22 !important;
        border-color: #30363d !important;
    }

    /* Code blocks */
    code {
        background-color: #161b22 !important;
        color: #79c0ff !important;
    }

    pre {
        background-color: #161b22 !important;
    }

    /* Multiselect */
    [data-baseweb="tag"] {
        background-color: #30363d !important;
    }

    /* Mobile responsiveness - Dark mode */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem !important;
        }

        /* Stack columns on mobile */
        .stColumns {
            flex-direction: column !important;
        }

        /* Make metrics stack vertically */
        [data-testid="metric-container"] {
            margin-bottom: 1rem;
        }

        /* Ensure charts are responsive */
        .js-plotly-plot {
            width: 100% !important;
        }

        /* Make tables scrollable */
        [data-testid="stDataFrame"] {
            overflow-x: auto;
        }

        /* Adjust button sizes */
        .stButton > button {
            width: 100%;
            margin-bottom: 0.5rem;
        }

        /* Stack sidebar filters */
        [data-testid="stSidebar"] {
            width: 100% !important;
        }
    }
    </style>
    """


def get_light_mode_css() -> str:
    """Return CSS for light mode styling (minimal overrides)."""
    return """
    <style>
    /* Light mode - use default Streamlit styles with minor enhancements */
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

    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }

        /* Stack columns on mobile */
        .stColumns {
            flex-direction: column !important;
        }

        /* Make metrics stack vertically */
        [data-testid="metric-container"] {
            margin-bottom: 1rem;
        }

        /* Ensure charts are responsive */
        .js-plotly-plot {
            width: 100% !important;
        }

        /* Make tables scrollable */
        [data-testid="stDataFrame"] {
            overflow-x: auto;
        }
    }
    </style>
    """


def initialize_theme():
    """Initialize theme state in session."""
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False


def apply_theme():
    """Apply the current theme based on session state."""
    initialize_theme()

    if st.session_state.dark_mode:
        st.markdown(get_dark_mode_css(), unsafe_allow_html=True)
    else:
        st.markdown(get_light_mode_css(), unsafe_allow_html=True)


def toggle_theme():
    """Toggle between dark and light mode."""
    st.session_state.dark_mode = not st.session_state.dark_mode


def render_theme_toggle():
    """Render theme toggle button in sidebar."""
    initialize_theme()

    with st.sidebar:
        st.divider()

        # Theme toggle button
        current_theme = "🌙 Dark Mode" if st.session_state.dark_mode else "☀️ Light Mode"

        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption("**Theme**")
        with col2:
            if st.button("🔄", help="Toggle theme", key="theme_toggle_btn"):
                toggle_theme()
                st.rerun()

        st.caption(f"Current: {current_theme}")


def get_plotly_template():
    """Get the appropriate Plotly template based on current theme."""
    initialize_theme()
    return "plotly_dark" if st.session_state.dark_mode else "plotly_white"


def apply_plot_theme(fig):
    """
    Apply the current theme to a Plotly figure with transparent background.
    This ensures the plot blends seamlessly with the Streamlit app background.
    """
    initialize_theme()
    
    if st.session_state.dark_mode:
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#fafafa"),
            xaxis=dict(gridcolor="#30363d"),
            yaxis=dict(gridcolor="#30363d"),
        )
    else:
        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )