# Quick Start Guide - What Do I Actually Need?

## TL;DR

**Just want to run evaluations?**
```bash
python start_all.py
# Choose option 2 (Development)
# Then: python core/evaluate.py
```

**That's it!** Everything else is optional.

---

## Three Simple Modes

### 🟢 Mode 1: MINIMAL (2 terminals)
**Use for:** Quick testing, fast iterations

```bash
# Terminal 1
python start_server.py

# Terminal 2
python core/evaluate.py
```

**You get:**
- ✅ Run evaluations
- ✅ Save results to database
- ❌ No dashboard UI
- ❌ No observability

**Time to start:** 30 seconds

---

### 🟡 Mode 2: DEVELOPMENT (3 terminals) ⭐ RECOMMENDED
**Use for:** Daily development, viewing results

```bash
# Terminal 1
python start_server.py

# Terminal 2
python scripts/start_api.py

# Terminal 3
python scripts/start_dashboard.py

# Then run evals:
python core/evaluate.py
```

**You get:**
- ✅ Run evaluations
- ✅ Dashboard UI (http://localhost:8501)
- ✅ View results visually
- ❌ No observability

**Time to start:** 1 minute

**OR use unified launcher:**
```bash
python start_all.py
# Choose option 2
```

---

### 🔴 Mode 3: FULL STACK (4 terminals)
**Use for:** Debugging, demos, Twitter screenshots

```bash
# Terminals 1-3: Same as Development mode

# Terminal 4
python scripts/start_phoenix.py

# Then run evals:
python core/evaluate.py
```

**You get:**
- ✅ Everything from Development
- ✅ Phoenix traces (http://localhost:6006)
- ✅ Debug performance issues
- ✅ View exact prompts/responses

**Time to start:** 2 minutes

**OR use unified launcher:**
```bash
python start_all.py
# Choose option 3
```

---

## Script Breakdown - What Does Each Do?

| Script | What It Does | When You Need It |
|--------|-------------|------------------|
| **start_server.py** | LiteLLM proxy (routes model calls) | **ALWAYS** (required for evals) |
| **scripts/start_api.py** | FastAPI backend (powers dashboard) | When using dashboard |
| **scripts/start_dashboard.py** | Streamlit UI (visual interface) | When viewing results |
| **scripts/start_phoenix.py** | Phoenix server (observability) | When debugging performance |
| **core/evaluate.py** | Direct evaluation (runs models) | **Main way to run evals** |
| **scripts/run_full_eval.py** | API-triggered eval (alternative) | Optional (redundant with core/evaluate.py) |

---

## Visual Dependency Map

```
┌─────────────────────────────────────────────────────────┐
│  MINIMAL MODE                                           │
│  ┌───────────────┐         ┌──────────────┐           │
│  │ start_server  │────────>│ evaluate.py  │           │
│  │  (LiteLLM)    │         │              │           │
│  └───────────────┘         └──────────────┘           │
│         ↓                                              │
│    Azure AI / OpenAI / Anthropic                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  DEVELOPMENT MODE (Recommended)                         │
│  ┌───────────────┐         ┌──────────────┐           │
│  │ start_server  │────────>│ evaluate.py  │           │
│  │  (LiteLLM)    │         │              │           │
│  └───────────────┘         └──────┬───────┘           │
│         ↓                          ↓                    │
│    Azure AI / etc.          ┌──────────────┐           │
│                             │  start_api   │           │
│                             │  (FastAPI)   │           │
│                             └──────┬───────┘           │
│                                    ↓                    │
│                             ┌──────────────┐           │
│                             │  dashboard   │           │
│                             │ (Streamlit)  │           │
│                             └──────────────┘           │
│                             http://localhost:8501       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  FULL STACK MODE                                        │
│  (Same as Development + Phoenix)                        │
│                                                         │
│  ┌──────────────┐                                      │
│  │ start_phoenix│                                      │
│  │  (Phoenix)   │<────── receives traces               │
│  └──────┬───────┘                                      │
│         ↓                                               │
│  http://localhost:6006                                  │
│         ↑                                               │
│  ┌──────────────┐                                      │
│  │ evaluate.py  │─────── sends traces                  │
│  │              │                                      │
│  └──────────────┘                                      │
└─────────────────────────────────────────────────────────┘
```

---

## Common Questions

### Q: Do I need all 6 scripts running?
**A:** NO! Minimum is 2 (LiteLLM + evaluate.py), recommended is 3 (add FastAPI + Streamlit for UI).

### Q: What's the difference between evaluate.py and run_full_eval.py?
**A:**
- `core/evaluate.py` - Direct evaluation (simpler, faster)
- `scripts/run_full_eval.py` - Triggers evaluation via FastAPI (adds extra layer)

**Use evaluate.py** - it's simpler and does the same thing.

### Q: When do I need Phoenix?
**A:** Only when:
- Debugging slow evaluations
- Inspecting exact prompts/responses
- Taking screenshots for Twitter
- Showing traces in demos

For daily development, skip it.

### Q: Can I stop using Phoenix entirely?
**A:** Yes! Edit `core/evaluate.py`, comment out lines 19-21:
```python
# phoenix_session = initialize_phoenix(launch_server=True, enable_tracing=True)
```

Trade-off: Lose observability, but faster startup.

### Q: What if I just want to see results?
**A:**
1. Start Development mode (3 terminals)
2. Open http://localhost:8501
3. Results from previous evals are already there!

No need to run new evaluations just to view results.

---

## My Recommendation for You

### Daily Workflow

**Morning (start once):**
```bash
python start_all.py
# Choose option 2 (Development)
```

**Throughout the day (run as needed):**
```bash
python core/evaluate.py
```

**Evening (when debugging):**
```bash
# Add Phoenix in separate terminal if needed
python scripts/start_phoenix.py
```

**Benefits:**
- Only start stack once per day
- Run evals with single command
- Add Phoenix only when debugging

---

## Simplified Commands Cheat Sheet

```bash
# START EVERYTHING (recommended)
python start_all.py

# RUN EVALUATION
python core/evaluate.py

# VIEW RESULTS
# Open: http://localhost:8501

# DEBUG WITH TRACES (optional)
python scripts/start_phoenix.py
# Open: http://localhost:6006
```

**That's it!** 4 commands total.

---

## Access Points Reference

| Service | URL | When It's Running |
|---------|-----|-------------------|
| **Streamlit Dashboard** | http://localhost:8501 | After start_dashboard.py |
| **FastAPI Docs** | http://localhost:8000/docs | After start_api.py |
| **LiteLLM Proxy** | http://localhost:4000 | After start_server.py |
| **Phoenix UI** | http://localhost:6006 | After start_phoenix.py |

---

## Troubleshooting

**"Too many terminals to manage!"**
→ Use `start_all.py` - opens everything automatically

**"I don't need the dashboard"**
→ Skip start_api.py and start_dashboard.py, just run LiteLLM + evaluate.py

**"Phoenix slows down startup"**
→ Don't run start_phoenix.py, it's optional

**"Which evaluation script should I use?"**
→ Use `core/evaluate.py` (simpler and more direct)

---

## Next Steps

1. ✅ Try Development mode: `python start_all.py` (option 2)
2. ✅ Run evaluation: `python core/evaluate.py`
3. ✅ View results: http://localhost:8501
4. ✅ Add Phoenix only when needed for debugging

Keep it simple! You don't need all 6 scripts running at once.

---

**Questions?** Check:
- `docs/SIMPLIFIED_USAGE.md` - Detailed breakdown
- `docs/PHOENIX_USAGE.md` - Phoenix-specific guide
- `DAY8_COMPLETE.md` - What was implemented on Day 8
