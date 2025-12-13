# Eval Dashboard 
Catch model drift before it kills your product.


## Daily Progress

| Date       | What I Shipped                          | Link/Post |
|------------|-----------------------------------------|---------|
| Day 0      | Repo + announcement                     | [Twitter thread](https://x.com/AICareerAcc/status/1996854594539000097) |
| Day 1      | Golden dataset + LiteLLM setup          | [Twitter thread](https://x.com/AICareerAcc/status/1998060139556065392)  |
| Day 2      | Auto Evaluation                         | [Twitter thread](https://x.com/AICareerAcc/status/1998294310358515855)         |
| Day 3      | Persistent logging with SQLAlchemy      | [Twitter thread](https://x.com/AICareerAcc/status/1998688624607723935)   |
| Day 4      | FastAPI Backend + GitHub Actions CI/CD  | [Twitter thread](https://x.com/AICareerAcc/status/1998926858851901575) |
| Day 5      | Streamlit Dashboard v1 (3 pages + drift detection) | [Twitter thread](https://x.com/AICareerAcc/status/1999841237365572001) |

## Project Log

### Day 0 – Just shipped
Repo created. 14-day public build starts NOW.

### Day 1: Golden dataset + LiteLLM integration

*   **Golden Dataset Creation**:
    *   Generated an initial "golden dataset" containing 50 questions to serve as a baseline for model evaluation.
    *   The questions were created using GPT and cover a diverse range of categories: reasoning, math, coding, hallucination, RAG, instruction-following, and safety.
    *   **Note**: For a real-world application, this dataset would be replaced by a custom, use-case-specific set of prompts and expected outcomes.

*   **LiteLLM Integration**:
    *   Set up and configured `litellm` to act as a unified interface for multiple LLM providers.
    *   The initial configuration includes 11 models from Azure OpenAI, OpenAI, Anthropic, and DeepSeek.
    *   Initial connection tests to all configured models were successful.

*   **Initial Findings**:
    *   An interesting quirk was discovered during testing: the model deployed as `azure/healthApp-gpt-5-chat` responded by identifying itself as a Claude model. This will be an interesting point to investigate further.

    ![Response: Hello!I am working correctly
    My model name is **Claude 3.5 Sonnet**.](docs/images/Day1-1.png)

### Day 2 – Automatic Evaluation Harness (Parallel, Scalable, Fast)

**Goal:** Auto-evaluate any model against a Golden Dataset.

---

#### 1. `judge.py`

Implemented a lightweight judge function using **GPT-4o-mini** (via LiteLLM proxy).

- Compares a model’s output to the `expected_output` from the dataset  
- Returns:  
  - **score (0–1)**  
  - **reasoning trace**  

Creates a universal, model-agnostic evaluation pipeline.

---

#### 2. Evaluation Pipeline (Two Versions in One Day)

##### **v1 – `evaluate_sequential.py`**
- Fully sequential — extremely slow  
- **500 calls × 5–15s = 42–125 minutes**  
- 😡😡😒😒

##### **v2 – `evaluate.py`**
Refactored into a **parallel evaluation harness** using:

- `ThreadPoolExecutor` for concurrent question evaluation  
- Parallelism across **both models and questions**  

**Performance Jump**
- Parallel: **5 questions at a time × 3 models → 8–15 minutes**  
- **~8× faster 🚀**  
- 🥰🥰😍😍

---

#### 3. Scalable by Design

- Add any model to **LiteLLM** → instantly evaluatable  
- Add a new question to **CSV** → automatically included  
- Zero additional configuration required  

---

#### 4. Next Steps

- Category-based metrics  
- Dashboard visualization  
- Drift detection (daily/weekly model regression alerts)

![Evaluate parallelly](docs/images/Day2-1.png)

### Day 3 – Persistent Logging (SQLite + SQLAlchemy)


#### What We Built

**Production-Ready Database Layer with SQLAlchemy ORM:**

Two-table schema designed for queryability and drift detection:

- **`runs` table**: Aggregate metrics per evaluation run
  - Model name, timestamp, git commit hash, accuracy, avg latency, total cost, evaluation time
  - Each row = one complete model evaluation (all 50 questions)

- **`evaluations` table**: Individual question results
  - Question ID, category, model response, judge score, judge reasoning, latency, estimated cost
  - Linked to runs via foreign key (one-to-many relationship)

**Key Features:**

💰 **Cost Estimation**
- Per-question cost tracking based on model pricing tiers
- Foundation for token-based pricing (upgrade path ready)
- Answers "how much did this eval run cost?"

🔍 **Query Utilities (`query_db.py`)**
- Show recent runs across all models
- Drill down into individual run details
- Model evaluation history over time
- Drift analysis: compare latest vs best historical run

**Integration:**
- `evaluate.py` saves to database after each model completes
- Non-breaking: JSON files still generated as backup
- Auto-initialization on first run
- Graceful error handling (eval continues if DB save fails)

---

#### Results

We validated the system by running 11 frontier models on 50 questions. The database handled 550 concurrent evaluations flawlessly. Here's what we learned:

**Model Performance Leaderboard:**

| Rank | Model | Accuracy | Avg Latency | Total Cost | Notes |
|------|-------|----------|-------------|------------|-------|
| 🥇 | claude-sonnet-4-5 | 88.8% | 5.07s | $0.055 | Best overall |
| 🥈 | grok-3 | 83.2% | 7.88s | $0.025 | Best value |
| 🥉 | claude-opus-4-5 | 82.3% | 5.97s | $0.288 | Most expensive |
| 4 | gpt-4o | 81.8% | 3.40s | $0.084 | Fastest quality model |
| 5 | gpt-5-chat | 81.4% | 5.73s | $0.106 | - |
| 6 | gpt-4o-mini | 80.8% | 2.64s | $0.090 | - |
| 7 | claude-haiku-4-5 | 79.8% | 2.00s | $0.004 | Cheapest |
| 8 | DeepSeek-V3.1 | 77.8% | 8.21s | $0.021 | - |
| 9 | Kimi-K2-Thinking | 52.6% | 5.00s | $0.005 | "Thinking" optional |
| 10 | Mistral-Large-3 | 31.4% | 18.69s | $0.008 | Slow + inaccurate |
| 💀 | Llama-4-Maverick | 0.0% | timeout | $0.000 | All requests timed out |

**Key Insights:**

- 💰 **Best ROI**: grok-3 delivered 83.2% accuracy for $0.025 (half the cost of GPT-4o)
- ⚡ **Speed King**: claude-haiku-4-5 averaged 2s per question (10% less accurate than Sonnet)
- 🐌 **Timeout Issues**: Llama-4-Maverick had 50/50 connection timeouts (model backend unavailable)
- 💸 **Cost Trap**: claude-opus cost 5× more than Sonnet for 6% LESS accuracy
- 🎯 **Sweet Spot**: claude-sonnet-4-5 = best accuracy/cost/speed balance

**Evaluation Stats:**
- **Total evaluations**: 11 models × 50 questions = 550
- **Runtime**: 10 minutes (parallel execution)
- **Total API cost**: ~$0.70
- **Database size**: 32KB
- **Git commit**: `574da7d` (all runs tagged)

**What This Proves:**
- ✅ Database handles concurrent writes across multiple threads
- ✅ Git commit tracking captures reproducibility data
- ✅ Cost estimation reveals budget surprises early
- ✅ Identifies unreliable models in minutes (not days in production)

---

#### How to Use It

**Run a full evaluation:**
```bash
python evaluate.py
# Evaluates all 11 models, saves to database + JSON backup
```

**Query the database:**
```bash
# Show recent runs
python query_db.py

# Detailed results for a specific run
python query_db.py run 5

# Model evaluation history
python query_db.py model gpt-4o

# Drift detection (compare latest vs best run)
python query_db.py drift claude-sonnet-4-5
```

**Quick test (5 questions, 1 model):**
```bash
python test_db.py
# Validates database integration in ~60 seconds
```

---

#### Migration to Postgres

Switch from SQLite to Postgres with **zero code changes**:

```bash
# .env file - SQLite (default)
DATABASE_URL=sqlite:///eval_dashboard.db

# .env file - Postgres (production)
DATABASE_URL=postgresql://user:password@localhost:5432/eval_dashboard
```

SQLAlchemy handles the dialect automatically. Just change the connection string.

---

### Day 4 – FastAPI Backend + GitHub Actions CI/CD

Built REST API and automated CI/CD pipeline for continuous model evaluation.

#### FastAPI Backend (9 Endpoints)

**Core:**
- `POST /run-evaluation` – Trigger eval with webhook callback (background task)
- `GET /runs` – List all runs (paginated, filterable)
- `GET /run/{id}` – Detailed results with category breakdown

**Enhanced:**
- `GET /models` – Model leaderboard with stats
- `GET /drift/{model}` – Drift detection (latest vs best accuracy)
- `GET /stats` – Dashboard summary
- `GET /health` – Health check

**Features:**
- Background tasks (non-blocking evaluations)
- Webhook callbacks (POST results when done)
- Auto docs at `/docs`
- ~100ms response time for queries

**Usage:**
```bash
python start_api.py  # Start server at http://127.0.0.1:8000
python test_api.py   # Test all endpoints
```
![FASTAPIs](docs/images/Day4-2.png)
---

#### GitHub Actions CI/CD

**Quick Eval (every push):**
- 3 models × 10 questions = ~2 min
- Fails if accuracy drops >10%
- Posts results on PRs

**Full Eval (manual only):**
- 7 models × 50 questions = ~15 min
- Artifacts saved for 30 days

**Result:** Catches regressions 30 seconds after merge. No deployment needed.

See `GITHUB_ACTIONS_SETUP.md` for detailed setup guide.
![GITHUB CICD](docs/images/Day4-1.png)
---

### Day 5 – Streamlit Dashboard v1 (Visualization + Drift Detection)

**Goal:** Production-ready dashboard with real-time model monitoring.

**What We Built:**
- **3-page Streamlit dashboard** with FastAPI integration
  - **Home**: Accuracy trends over time with automatic drift alerts (🔴 flags drops >3%)
  - **Run Detail**: Question-level breakdown with judge reasoning, filterable by category, CSV/JSON export
  - **Model Comparison**: Leaderboard, performance heatmap, cost vs accuracy scatter plot, category winners

**Key Features:**
- Real-time drift detection with configurable threshold slider
- Interactive charts (line plots, heatmaps, scatter plots)
- Export functionality for all data views
- Recommendation engine for model selection
- API health monitoring

**Quick Start:**
```bash
# Terminal 1 - Start API
python scripts/start_api.py

# Terminal 2 - Launch Dashboard
python scripts/start_dashboard.py
# Opens at http://localhost:8501
```

**Impact:** From raw data to executive-ready visualizations. Now stakeholders can SEE model drift in real-time.

![Dashboard Screenshots](docs/images/Day5-1.png)

---

#### What's Next (Day 6+)
- Slack/email webhook alerts
- Automatic deployment blocking on regression

---

## Built in Public 🏗️
Follow the journey on Twitter/X, LinkedIn
Substack -> AI Career Accelerator

## Sponsors ❤️
Love this? Fuel the build:
[!GitHub Sponsors](https://github.com/sponsors/AI-Career-Accelerator)
<!-- [!BuyMeACoffee](https://www.buymeacoffee.com/AI-Career-Accelerator) -->

MIT License • Star if this helps you ship better AI
