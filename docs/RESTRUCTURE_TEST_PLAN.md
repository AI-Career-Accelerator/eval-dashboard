# Restructure Test Plan

This document provides comprehensive testing instructions after the repository restructure.

## Pre-Test Checklist

Before testing, verify the new structure:

```bash
# Check directory structure
ls -la

# Expected directories:
# ├── api/
# ├── core/
# ├── scripts/
# ├── tests/
# ├── data/
# ├── docs/
# ├── config/
# └── (old files remain at root for backup)
```

---

## Test Suite

### Test 1: Core Database Module

**Test core/db.py initialization and basic operations**

```bash
# Initialize database (creates data/eval_dashboard.db)
python -c "from core.db import init_db; init_db()"

# Expected output:
# [OK] Database initialized: sqlite:///data/eval_dashboard.db

# Verify database created
ls data/eval_dashboard.db
```

**✅ Pass criteria:**
- Database file created at `data/eval_dashboard.db`
- No import errors
- No SQL errors

---

### Test 2: Core Judge Module

**Test core/judge.py scoring functionality**

```bash
python -c "from core.judge import score_answer; print(score_answer('8', '8'))"
```

**✅ Pass criteria:**
- Returns tuple: `(score, reasoning)`
- Score is between 0.0 and 1.0
- No import errors

---

### Test 3: Database Test Script

**Run tests/test_db.py**

```bash
python tests/test_db.py
```

**✅ Pass criteria:**
- Connects to LiteLLM proxy successfully
- Evaluates 1 model on 5 questions
- Saves results to database
- Displays summary with accuracy and cost
- No import errors

**Expected output:**
```
Starting Day 3 Database Integration Test
========================================
Testing with 1 model(s) on 5 question(s)

[MODEL 1/1] Evaluating gpt-4o-mini...
...
✓ Run #X saved to database

TEST SUMMARY
============
Models tested: 1
Best model: gpt-4o-mini (XX.X% accuracy)
```

---

### Test 4: Query Database Script

**Run scripts/query_db.py**

```bash
# Show recent runs
python scripts/query_db.py

# Show specific run details
python scripts/query_db.py run 1

# Show model history
python scripts/query_db.py model gpt-4o-mini

# Show drift analysis
python scripts/query_db.py drift gpt-4o-mini
```

**✅ Pass criteria:**
- Displays recent runs correctly
- Run details show all questions
- Model history shows all runs for that model
- Drift analysis calculates correctly
- No import errors

---

### Test 5: FastAPI Backend

**Start API server**

```bash
python scripts/start_api.py
```

**Open browser:**
- http://127.0.0.1:8000 (API root)
- http://127.0.0.1:8000/docs (Interactive docs)

**Test endpoints in browser:**
1. GET `/health` - Should return status "healthy"
2. GET `/models` - Should return model statistics
3. GET `/runs` - Should return list of runs
4. GET `/stats` - Should return dashboard stats

**✅ Pass criteria:**
- Server starts without errors
- All endpoints return 200 status
- Interactive docs load correctly
- No import errors

---

### Test 6: API Test Suite

**Run tests/test_api.py** (make sure API server is running first)

```bash
# In terminal 1:
python scripts/start_api.py

# In terminal 2:
python tests/test_api.py
```

**✅ Pass criteria:**
- All 7 tests pass
- Health check returns "healthy"
- Models endpoint returns data
- Runs endpoint returns paginated results
- No connection errors

**Expected output:**
```
🧪 Eval Dashboard API Test Suite
...
==================================================
Test Results Summary
==================================================
✅ PASSED: Health Check
✅ PASSED: Dashboard Stats
✅ PASSED: Models List
✅ PASSED: Runs List
✅ PASSED: Run Detail
✅ PASSED: Drift Analysis
⏭️  SKIPPED: Run Evaluation (manual trigger)
==================================================
Total: 6/7 tests passed (85.7%)
```

---

### Test 7: Full Evaluation (Optional - takes ~10 min)

**Run core/evaluate.py for full model evaluation**

```bash
# Make sure LiteLLM proxy is running
python core/evaluate.py
```

**✅ Pass criteria:**
- Evaluates all configured models
- Saves results to `data/eval_dashboard.db`
- Creates backup JSON in `data/evaluation_results_*.json`
- Displays summary with accuracy, latency, cost
- No import errors

---

### Test 8: Model Connection Test

**Test LiteLLM proxy connectivity**

```bash
python scripts/test_model_connections.py
```

**✅ Pass criteria:**
- Tests all configured models
- Shows success/failure for each
- Displays response time
- Identifies broken models

---

### Test 9: GitHub Actions Workflow (Optional)

**Test CI/CD pipeline**

```bash
# Stage all changes
git add .

# Commit
git commit -m "Restructure repository - Option 1 (Clean & Simple)"

# Push to trigger workflow
git push origin main
```

**Check GitHub Actions tab:**
- Workflow should start automatically
- Quick evaluation job should complete in ~2-3 minutes
- Database artifact should be uploaded

**✅ Pass criteria:**
- Workflow runs without errors
- Evaluation completes successfully
- Artifact contains `data/eval_dashboard.db`

---

## Common Issues & Solutions

### Issue 1: ModuleNotFoundError

**Error:** `ModuleNotFoundError: No module named 'core'`

**Solution:**
```bash
# Make sure you're running from project root
cd /path/to/eval-dashboard

# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue 2: Database Not Found

**Error:** `sqlite3.OperationalError: unable to open database file`

**Solution:**
```bash
# Make sure data directory exists
mkdir -p data

# Initialize database
python -c "from core.db import init_db; init_db()"
```

### Issue 3: Golden Dataset Not Found

**Error:** `FileNotFoundError: [Errno 2] No such file or directory: 'data/golden_dataset.csv'`

**Solution:**
```bash
# Verify dataset is in data directory
ls data/golden_dataset.csv

# If not found, it might still be at root
mv golden_dataset.csv data/
```

### Issue 4: LiteLLM Proxy Connection Refused

**Error:** `requests.exceptions.ConnectionError: Connection refused`

**Solution:**
```bash
# Start LiteLLM proxy first
litellm --config config/litellm_config.yaml --port 4000

# Then run tests in another terminal
```

---

## Verification Checklist

After all tests pass, verify:

- [ ] ✅ Database created at `data/eval_dashboard.db`
- [ ] ✅ All imports work from new locations
- [ ] ✅ API server starts without errors
- [ ] ✅ Tests run successfully
- [ ] ✅ Query scripts work correctly
- [ ] ✅ GitHub Actions workflow passes (if pushed)
- [ ] ✅ No broken file paths
- [ ] ✅ README images display correctly

---

## Rollback Plan (If Tests Fail)

If critical issues occur:

```bash
# Restore from git (if changes committed)
git reset --hard HEAD^

# Or manually restore files
# (All original files were kept at root level)
```

---

## Performance Benchmarks

Expected performance after restructure:

| Test | Expected Time | Status |
|------|--------------|--------|
| Database init | < 1 second | Should be instant |
| test_db.py | ~30-60 seconds | 1 model, 5 questions |
| test_api.py | ~5-10 seconds | API health checks |
| Full evaluation | ~10-15 minutes | 11 models, 50 questions |
| GitHub Actions (Quick) | ~2-3 minutes | 3 models, 10 questions |

---

## Success Criteria

The restructure is successful if:

1. ✅ All test scripts run without import errors
2. ✅ Database is created in `data/` directory
3. ✅ API server starts and all endpoints work
4. ✅ README images display correctly on GitHub
5. ✅ GitHub Actions workflow completes successfully
6. ✅ No functionality is broken
7. ✅ Code is cleaner and better organized

---

## Next Steps After Testing

Once all tests pass:

1. **Commit changes:**
   ```bash
   git add .
   git commit -m "Restructure: Option 1 (Clean & Simple) - All tests passing"
   git push origin main
   ```

2. **Update documentation:**
   - Update `docs/GITHUB_ACTIONS_SETUP.md` if needed
   - Add migration notes to README if helpful

3. **Clean up (optional):**
   - After verifying everything works for a few days
   - Consider removing old backup files (mainbk.py, evaluate_sequential.py, etc.)

---

**Test Plan Version:** 1.0
**Created:** 2025-12-11
**Structure:** Option 1 (Clean & Simple)
