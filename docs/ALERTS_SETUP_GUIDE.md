# Drift Detection & Alerts Setup Guide

Complete guide to setting up automated drift detection and alerts for your Eval Dashboard.

---

## Overview

The drift detection system monitors model performance and sends alerts when accuracy drops below acceptable thresholds. It supports three alert channels:

1. **Generic HTTP Webhook** - POST to any URL
2. **Discord Webhook** - Rich notifications in Discord
3. **Email (SMTP)** - Professional HTML emails

---

## Quick Start

### 1. Configure Environment Variables

Copy `.env.example` to `.env` (if not already done) and add your alert configuration:

```bash
# Drift threshold (percentage drop that triggers alerts)
DRIFT_THRESHOLD_PERCENT=5

# Choose one or more alert channels below:

# Option 1: Generic HTTP Webhook
WEBHOOK_URL=https://webhook.site/your-unique-url

# Option 2: Discord Webhook
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123/abc

# Option 3: Email Alerts
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_TO=recipient@example.com
```

### 2. Test Your Configuration

```bash
# Check all models for drift (no alerts sent)
python scripts/test_drift_alerts.py

# Test alerts for a specific model
python scripts/test_drift_alerts.py gpt-4o
```

---

## Alert Channel Setup

### Option 1: Generic HTTP Webhook

**Use Case:** Integrate with Zapier, n8n, Make.com, or custom endpoints

**Setup:**
1. Get a webhook URL from your service:
   - Webhook.site (testing): https://webhook.site
   - Zapier: Create a "Webhook" trigger
   - n8n: Create a "Webhook" node
   - Custom: Deploy your own endpoint

2. Add to `.env`:
   ```bash
   WEBHOOK_URL=https://your-webhook-url.com/endpoint
   ```

**Payload Format:**
```json
{
  "model": "gpt-4o",
  "drift_detected": true,
  "latest_run": {
    "id": 123,
    "accuracy": 76.8,
    "timestamp": "2025-01-15T10:30:00",
    "cost": 0.084,
    "latency": 3.4
  },
  "best_run": {
    "id": 98,
    "accuracy": 81.8,
    "timestamp": "2025-01-10T14:20:00"
  },
  "drift_percentage": 5.0,
  "threshold_percent": 5.0,
  "timestamp": "2025-01-15T10:30:15"
}
```

---

### Option 2: Discord Webhook

**Use Case:** Real-time notifications in your Discord server

**Setup:**
1. Go to your Discord server
2. Navigate to: Server Settings → Integrations → Webhooks
3. Click "New Webhook"
4. Choose a channel (e.g., #ai-alerts)
5. Copy the webhook URL
6. Add to `.env`:
   ```bash
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1234567890/abcdefghijklmnop
   ```

**What You'll See:**
- 🔴 **Red embed** when drift is detected
- 🟢 **Green embed** when model is healthy
- Detailed metrics table
- Timestamp of detection

**Example Alert:**
```
🚨 Model Drift Alert: gpt-4o

Accuracy dropped by 5.0%
Current: 76.8% → Best: 81.8%

Latest Accuracy: 76.8%
Best Accuracy: 81.8%
Drift: 5.0%
Avg Latency: 3.4s
Cost: $0.084
Run ID: #123
```

---

### Option 3: Email (SMTP)

**Use Case:** Professional reports for team/management

**Setup for Gmail:**

1. **Enable 2-Factor Authentication** on your Google account
   - Go to: https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Select app: "Mail"
   - Select device: "Other" (type "Eval Dashboard")
   - Click "Generate"
   - Copy the 16-character password

3. **Add to `.env`:**
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=abcd efgh ijkl mnop  # 16-char app password
   ALERT_EMAIL_TO=recipient@example.com
   ```

**Alternative SMTP Providers:**

**SendGrid:**
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
ALERT_EMAIL_TO=recipient@example.com
```

**Mailgun:**
```bash
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@your-domain.mailgun.org
SMTP_PASSWORD=your-mailgun-password
ALERT_EMAIL_TO=recipient@example.com
```

**Email Format:**
- Professional HTML template
- Metrics comparison table
- Color-coded status (red for drift)
- Action items for investigation
- Full run details

---

## Testing Your Setup

### 1. Check Configuration Status

```bash
python scripts/test_drift_alerts.py
```

Output shows which channels are configured:
```
Generic Webhook: [CONFIGURED]
  URL: https://webhook.site/abc123

Discord Webhook: [NOT CONFIGURED]

Email Alerts: [CONFIGURED]
  From: your-email@gmail.com
  To: recipient@example.com
```

### 2. Test Specific Model

```bash
# This will send actual alerts if drift is detected
python scripts/test_drift_alerts.py gpt-4o
```

### 3. Test via API

```bash
# Start API server
python scripts/start_api.py

# In another terminal, test alerts
curl -X POST http://localhost:8000/test-alerts/gpt-4o?threshold=5.0
```

---

## How It Works

### Automatic Detection (Production)

Drift detection runs automatically after every evaluation:

1. **Run Evaluation:**
   ```bash
   python scripts/run_full_eval.py
   ```

2. **After Each Model Completes:**
   - Save results to database
   - Check latest accuracy vs. best historical accuracy
   - If drop ≥ threshold → Send alerts to all configured channels

3. **Alerts Fire Instantly:**
   - Webhook: POST request sent
   - Discord: Message posted to channel
   - Email: HTML email sent

### Manual Testing (Development)

Test drift detection without running full evaluations:

```bash
# Check all models
python scripts/test_drift_alerts.py

# Test specific model with alerts
python scripts/test_drift_alerts.py claude-sonnet-4-5
```

---

## Customization

### Adjust Drift Threshold

Change the threshold in `.env`:

```bash
# More sensitive (triggers at 3% drop)
DRIFT_THRESHOLD_PERCENT=3

# Less sensitive (triggers at 10% drop)
DRIFT_THRESHOLD_PERCENT=10
```

Or set per-request via API:

```bash
curl -X POST http://localhost:8000/test-alerts/gpt-4o?threshold=3.0
```

### Disable Specific Channels

Simply comment out or remove the environment variables:

```bash
# Disable webhook
# WEBHOOK_URL=https://...

# Keep Discord enabled
DISCORD_WEBHOOK_URL=https://discord.com/...

# Disable email
# SMTP_USER=...
```

---

## Troubleshooting

### Webhook Not Receiving Data

**Check:**
- URL is correct and accessible
- Service is expecting POST requests
- Content-Type: application/json is accepted

**Test:**
```bash
curl -X POST https://webhook.site/your-url \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### Discord Alert Not Appearing

**Check:**
- Webhook URL is complete (includes token)
- Channel permissions allow webhook messages
- Discord server is accessible

**Test:**
```bash
curl -X POST "https://discord.com/api/webhooks/..." \
  -H "Content-Type: application/json" \
  -d '{"content": "Test message"}'
```

### Email Not Sending

**Gmail Issues:**
- Verify 2FA is enabled
- Use App Password (not regular password)
- Check "Less secure app access" is NOT needed (use App Password instead)

**SMTP Errors:**
- Port 587 (TLS) is most common
- Some networks block port 25
- Check firewall/antivirus settings

**Test SMTP Connection:**
```python
import smtplib

server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'app-password')
server.quit()
print("SMTP connection successful!")
```

---

## Production Best Practices

### Security

1. **Never commit `.env` file** (already in `.gitignore`)
2. **Use environment variables** in production (not .env file)
3. **Rotate SMTP passwords** regularly
4. **Use dedicated email** for alerts (not personal)

### Alert Fatigue Prevention

1. **Set appropriate threshold** (5% is recommended)
2. **Don't alert on first run** (no baseline yet)
3. **Deduplicate alerts** (avoid multiple alerts for same issue)

### Monitoring

1. **Log all alert attempts** (successful and failed)
2. **Monitor alert delivery** (track webhook responses)
3. **Test alerts weekly** (ensure channels still work)

---

## Next Steps

1. ✅ Configure at least one alert channel
2. ✅ Test with `python scripts/test_drift_alerts.py <model>`
3. ✅ Run a full evaluation to see automatic alerts
4. 📊 Monitor your dashboard for drift trends
5. 🔔 Adjust thresholds based on your use case

---

## Support

- **Documentation:** See `README.md` for full project docs
- **Issues:** https://github.com/your-username/eval-dashboard/issues
- **Examples:** Check `docs/DAY6_TWEET.md` for usage examples

---

Built with ❤️ as part of the 14-day eval dashboard challenge.
