# GitHub Actions Setup Guide

This guide shows you how to set up GitHub Actions for automated model evaluations.

---

## Step 1: Add GitHub Secrets

Go to your repository: https://github.com/AI-Career-Accelerator/eval-dashboard

1. Click **Settings** (top right)
2. Click **Secrets and variables** > **Actions** (left sidebar)
3. Click **New repository secret** button
4. Add each secret below:

### Required Secrets

Copy the values from your `.env` file:

| Secret Name | Value from .env | Description |
|-------------|-----------------|-------------|
| `AZURE_API_KEY` | Your `AZURE_API_KEY` value | Main Azure API key for all services |
| `AZURE_API_BASE` | Your `AZURE_API_BASE` value | Azure OpenAI base URL |
| `AZURE_OPENAI_BASE` | Your `AZURE_OPENAI_BASE` value | Azure AI marketplace base URL |
| `AZURE_ANTHROPIC_BASE` | Your `AZURE_ANTHROPIC_BASE` value | Azure Anthropic (Claude) base URL |

---

## Step 2: Commit and Push the Workflow

```bash
# Stage the workflow file
git add .github/workflows/eval-on-push.yml

# Commit
git commit -m "Add GitHub Actions CI/CD with Azure models"

# Push to main branch (this will trigger the workflow)
git push origin main
```

---

## Step 3: Verify the Workflow Runs

1. Go to your repo: https://github.com/AI-Career-Accelerator/eval-dashboard
2. Click the **Actions** tab
3. You should see "Eval Dashboard CI" workflow running
4. Click on the running workflow to see live logs

---

## What the Workflow Does

### Job 1: Quick Evaluation (Every Push/PR)
- **Triggers**: Every push to main, every pull request
- **Models tested**: gpt-4o-mini, claude-sonnet-4-5, DeepSeek-V3.1
- **Questions**: 10 (subset for speed)
- **Duration**: ~2-3 minutes
- **Purpose**: Fast feedback, catches regressions early
- **Drift detection**: Fails if accuracy drops >10%

### Job 2: Full Evaluation (Manual Trigger Only)
- **Triggers**: Manual Trigger
- **Models tested**: gpt-4o-mini, gpt-4o, claude-sonnet-4-5, DeepSeek-V3.1, grok-3
- **Questions**: 50 (all questions)
- **Duration**: ~10-15 minutes
- **Purpose**: Comprehensive model comparison
- **Artifacts**: Full database available for download

---

## Workflow Features

✅ **Automatic drift detection** - Fails build if model accuracy regresses
✅ **PR comments** - Posts evaluation results directly on pull requests
✅ **Artifact storage** - Database saved for 30 days (downloadable)
✅ **Parallel execution** - Models evaluated concurrently for speed
✅ **Secure secrets** - API keys encrypted and never exposed in logs
✅ **Manual trigger** - Can run workflow manually via Actions tab

---

## Viewing Results

### In GitHub Actions Logs
1. Go to **Actions** tab
2. Click on a workflow run
3. Click on "Run Model Evaluations" job
4. Expand "Run lightweight evaluation (CI mode)" step
5. See detailed results with accuracy, latency, costs

### Download Artifacts
1. Scroll to bottom of workflow run page
2. Click "eval-results-{commit-sha}" under Artifacts
3. Download the database file
4. Query locally: `python query_db.py`

### PR Comments (for Pull Requests)
- Bot automatically posts results as a comment
- Shows: Model, Accuracy, Pass/Fail status
- Example:
  ```
  🤖 Eval Dashboard CI Results
  Model: gpt-4o-mini
  Accuracy: 84.50%
  Commit: a1b2c3d
  Questions: 10 (CI subset)
  ✅ Evaluation passed!
  ```

---

## Manual Workflow Trigger

To run the workflow manually without pushing code:

1. Go to **Actions** tab
2. Click **Eval Dashboard CI** in the left sidebar
3. Click **Run workflow** button (top right)
4. Select branch (usually `main`)
5. Click green **Run workflow** button

---

## Troubleshooting

### Workflow fails with "Secrets not found"
- Make sure you added all 4 secrets (AZURE_API_KEY, AZURE_API_BASE, etc.)
- Check spelling matches exactly (case-sensitive)

### LiteLLM proxy fails to start
- Check the "Check LiteLLM logs (on failure)" step in the workflow logs
- Usually means API key or base URL is incorrect

### Models timeout
- Some Azure AI models may be slower
- Workflow has 60-second timeout per question
- Consider removing slow models from quick CI job

### PR comments not working
- Only works on Pull Requests, not direct pushes
- Requires `github-script` action (already included)

---

## Cost Estimation

**Quick Evaluation (every push):**
- 3 models × 10 questions = 30 API calls
- Estimated cost: ~$0.02 per run

**Full Evaluation (manual trigger only):**
- 5 models × 50 questions = 250 API calls
- Estimated cost: ~$0.15 per run

**Monthly estimate (assuming 100 pushes/month):**
- Quick: 100 × $0.02 = $2.00
- Full: ~20 × $0.15 = $3.00
- **Total: ~$5/month**

---

## Next Steps

After setting up GitHub Actions:

1. **Test it**: Make a small commit and push to trigger the workflow
2. **Create a PR**: See the bot comment in action
3. **Check artifacts**: Download and explore the evaluation database
4. **Customize**: Edit `.github/workflows/eval-on-push.yml` to add/remove models
5. **Schedule**: Add scheduled runs (e.g., daily at 9am UTC)

---

## Security Notes

✅ **Secrets are encrypted** - GitHub encrypts all secrets at rest
✅ **Not visible in logs** - Secret values are automatically redacted (shown as `***`)
✅ **Fork protection** - Forks of your public repo CANNOT access your secrets
✅ **Audit trail** - GitHub logs all secret access

**Important:** Never commit `.env` file or hardcode API keys in code!

---

## Support

If you encounter issues:
1. Check the workflow logs in the Actions tab
2. Look for error messages in failed steps
3. Verify all secrets are added correctly
4. Check Azure API quotas/limits

---

**Ready to ship?** Add the secrets and push! 🚀
