# Streamlit Dashboard - Day 5

Interactive dashboard for AI model evaluation tracking and drift detection.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd dashboard
pip install -r requirements.txt
```

### 2. Start the FastAPI Backend (Required)

The dashboard requires the FastAPI backend to be running:

```bash
# From the project root
python scripts/start_api.py
```

The API should be accessible at http://127.0.0.1:8000

### 3. Launch the Dashboard

```bash
streamlit run app.py
```

The dashboard will open automatically in your browser at http://localhost:8501

## 📊 Dashboard Pages

### 1. Home Page (app.py)
- **Drift Detection Alerts**: Red/green indicators showing models with accuracy drops >3%
- **Accuracy Over Time Chart**: Interactive line chart tracking model performance trends
- **Summary Statistics**: Key metrics across all evaluations
- **Recent Runs Table**: Latest evaluation results

**Key Features:**
- Adjustable drift threshold (1-10%)
- Multi-model selection
- Interactive Plotly charts
- Real-time API health status

### 2. Run Detail (pages/1_Home.py → pages/2_Run_Detail.py)
- **Run Selector**: Choose specific evaluation runs to explore
- **Category Breakdown**: Performance analysis by question category
- **Question-Level Results**: Detailed view of every question with:
  - Model responses
  - Judge scores and reasoning
  - Latency and cost metrics
- **Export Options**: Download results as CSV or JSON

**Key Features:**
- Filter by category and score
- Sort by multiple metrics
- Expandable question cards
- Color-coded performance indicators

### 3. Model Comparison (pages/3_Model_Comparison.py)
- **Leaderboard Table**: Ranked comparison across all models
- **Performance Heatmap**: Normalized metrics visualization
- **Cost-Accuracy Trade-off**: Scatter plot with quadrant analysis
- **Detailed Metrics**: Tabbed views for accuracy, cost, latency
- **Winner Cards**: Best performers by category
- **Recommendation Engine**: Composite score for optimal model

**Key Features:**
- Customizable sorting and filtering
- Multi-dimensional analysis
- Visual heatmaps and charts
- Data-driven recommendations

## 🔧 API Integration

The dashboard uses `utils/api_client.py` to communicate with the FastAPI backend.

**Available Endpoints:**
- `GET /health` - System health check
- `GET /stats` - Dashboard statistics
- `GET /runs` - List evaluation runs (paginated)
- `GET /run/{id}` - Detailed run results
- `GET /models` - Model statistics
- `GET /drift/{model}` - Drift analysis
- `POST /run-evaluation` - Trigger new evaluation

## 📦 Dependencies

- **streamlit** - Dashboard framework
- **requests** - HTTP client for API calls
- **pandas** - Data manipulation
- **plotly** - Interactive charts
- **altair** - Additional visualizations

## 🎯 Day 5 Requirements Checklist

✅ **Home Page**: Accuracy over time line chart (red if drop >3%)
✅ **Run Detail**: Table with every question + judge reasoning
✅ **Model Comparison**: Matrix comparing models across metrics
✅ **FastAPI Integration**: All pages use HTTP requests to backend
✅ **Drift Detection**: Visual alerts for accuracy degradation

## 🐛 Troubleshooting

### "API Error" messages
- Ensure FastAPI backend is running: `python scripts/start_api.py`
- Check that LiteLLM proxy is available: `litellm --config config.yaml`

### "No evaluation runs found"
- Run an evaluation first: `python core/evaluate.py`
- Check database has data: `python scripts/query_db.py`

### Dashboard won't start
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: Requires Python 3.8+
- Try: `streamlit run app.py --server.port 8501`

## 📝 Next Steps (Day 6+)

- Add email/Slack webhook alerts for drift detection
- Implement real-time evaluation triggering from dashboard
- Add cost savings calculator
- Dark mode support
- Mobile responsive design

## 🎉 Built in Public - Day 5/14

Part of the 14-day Eval Dashboard build challenge.
