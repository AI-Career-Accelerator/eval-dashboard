# 🚀 Day 5 Complete - Launch Your Dashboard!

## Quick Launch (2 Steps)

### Step 1: Start the FastAPI Backend

Open a terminal and run:

```bash
python scripts/start_api.py
```

You should see:
```
✅ FastAPI server running at: http://127.0.0.1:8000
📚 API docs available at: http://127.0.0.1:8000/docs
```

**Keep this terminal open!**

### Step 2: Start the Streamlit Dashboard

Open a **NEW** terminal and run:

```bash
python scripts/start_dashboard.py
```

Or alternatively:

```bash
cd dashboard
streamlit run app.py
```

The dashboard will automatically open in your browser at **http://localhost:8501**

---

## 📊 What You Built Today

✅ **Complete Streamlit Dashboard with 3 pages:**

### 1. Home Page
- Drift detection alerts (🔴 red if accuracy drops >3%)
- Interactive accuracy-over-time line chart
- Summary statistics cards
- Recent runs table
- API health monitoring

### 2. Run Detail Page
- Run selector dropdown
- Category performance breakdown
- Question-level results with:
  - Model responses
  - Judge scores + reasoning
  - Latency & cost metrics
- Filter by category/score
- Export to CSV/JSON

### 3. Model Comparison Page
- Model leaderboard table
- Performance heatmap (normalized scores)
- Cost vs Accuracy scatter plot
- Detailed metrics tabs (Accuracy, Cost, Latency)
- Category winners (Most Accurate, Cost-Effective, Fastest)
- Recommendation engine

---

## 🎯 Day 5 Requirements - ALL COMPLETE!

✅ Pages: Home + Run Detail + Model Comparison
✅ Home: accuracy over time line chart (red if drop >3%)
✅ Run Detail: table with every question + judge reasoning
✅ Model Comparison: matrix comparing models
✅ Streamlit + FastAPI integration
✅ Drift detection with visual alerts

---

## 🧪 Testing Your Dashboard

Once both servers are running:

1. **Check Home Page**
   - See all your models plotted over time
   - Look for red/green drift indicators
   - Adjust the drift threshold slider

2. **Explore Run Detail**
   - Select a run from the dropdown
   - Expand question cards to see responses
   - Try filtering by category
   - Export results to CSV

3. **Compare Models**
   - View the leaderboard
   - Examine the heatmap
   - Check the cost-accuracy scatter plot
   - See which model is recommended

---

## 📸 Screenshot Time!

For your Day 5 tweet, capture:
- The Home page with drift alerts
- The accuracy chart with multiple models
- The Model Comparison heatmap

**Tweet Template:**
```
Day 5/14: Streamlit Dashboard v1 is LIVE 🚀

✅ Accuracy trends over time
✅ Drift detection (auto-flags >3% drops)
✅ Question-level breakdown
✅ Model comparison matrix

From 0 to production-ready in 5 days.

[15-second Loom demo]
[Screenshots]

#BuildInPublic #AI #Dashboard
```

---

## 🐛 Troubleshooting

**"API Error" in dashboard:**
- Make sure FastAPI is running: `python scripts/start_api.py`
- Check http://127.0.0.1:8000/health returns 200

**"No evaluation runs found":**
- Run evaluations first: `python core/evaluate.py`
- Check database: `python scripts/query_db.py`

**Dashboard won't start:**
- Install deps: `pip install -r dashboard/requirements.txt`
- Try: `streamlit run dashboard/app.py --server.port 8501`

---

## 📁 What Was Created

```
dashboard/
├── app.py                          # Main dashboard with navigation
├── requirements.txt                # Dependencies
├── README.md                       # Dashboard documentation
├── pages/
│   ├── 1_Home.py                  # Accuracy trends + drift alerts
│   ├── 2_Run_Detail.py            # Question-level breakdown
│   └── 3_Model_Comparison.py      # Model comparison matrix
└── utils/
    ├── __init__.py
    └── api_client.py              # FastAPI HTTP client

scripts/
└── start_dashboard.py             # Convenience launcher
```

---

## 🎉 Next Steps (Day 6)

Tomorrow: **Drift Detection & Alerts**
- Slack webhook integration
- Email notifications
- Automatic alerts when accuracy drops
- Red flag deployment blocking

**Ready to ship this!** 🚀
