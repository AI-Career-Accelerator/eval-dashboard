"""
Test script for drift detection and alerting system.
Demonstrates automatic drift detection with configurable webhooks.
"""
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.drift_detector import DriftDetector, check_model_drift
from core.db import get_recent_runs


def test_drift_detection():
    """
    Test drift detection for all models in the database.
    """
    print("=" * 80)
    print("DRIFT DETECTION TEST")
    print("=" * 80)
    print()

    # Get recent runs
    runs = get_recent_runs(limit=20)

    if not runs:
        print("[ERROR] No runs found in database. Run an evaluation first.")
        return

    # Get unique models
    models = list(set(run.model_name for run in runs))
    print(f"Found {len(models)} models in database:")
    for model in models:
        print(f"  - {model}")
    print()

    # Test each model
    detector = DriftDetector(threshold_percent=5.0)

    for model in models:
        print("-" * 80)
        print(f"Testing: {model}")
        print("-" * 80)

        # Check drift
        result = detector.check_drift(model)

        # Display results
        if result.get("drift_detected"):
            print(f"[ALERT] DRIFT DETECTED!")
            print(f"   Current Accuracy: {result['latest_run']['accuracy']}%")
            print(f"   Best Accuracy: {result['best_run']['accuracy']}%")
            print(f"   Drop: {result['drift_percentage']}%")
            print(f"   Threshold: {result['threshold_percent']}%")
        else:
            print(f"[OK] NO DRIFT - Model within acceptable range")
            if result.get("latest_run"):
                print(f"   Current Accuracy: {result['latest_run']['accuracy']}%")
                if result.get("best_run"):
                    print(f"   Best Accuracy: {result['best_run']['accuracy']}%")
                print(f"   Drift: {result.get('drift_percentage', 0)}%")

        print()

    print("=" * 80)
    print("ALERT CONFIGURATION STATUS")
    print("=" * 80)
    print()

    # Check which alert channels are configured
    webhook_configured = bool(os.getenv("WEBHOOK_URL"))
    discord_configured = bool(os.getenv("DISCORD_WEBHOOK_URL"))
    email_configured = all([
        os.getenv("SMTP_USER"),
        os.getenv("SMTP_PASSWORD"),
        os.getenv("ALERT_EMAIL_TO")
    ])

    print(f"Generic Webhook: {'[CONFIGURED]' if webhook_configured else '[NOT CONFIGURED]'}")
    if webhook_configured:
        print(f"  URL: {os.getenv('WEBHOOK_URL')}")

    print(f"Discord Webhook: {'[CONFIGURED]' if discord_configured else '[NOT CONFIGURED]'}")
    if discord_configured:
        print(f"  URL: {os.getenv('DISCORD_WEBHOOK_URL')[:50]}...")

    print(f"Email Alerts:    {'[CONFIGURED]' if email_configured else '[NOT CONFIGURED]'}")
    if email_configured:
        print(f"  From: {os.getenv('SMTP_USER')}")
        print(f"  To: {os.getenv('ALERT_EMAIL_TO')}")

    print()

    if not any([webhook_configured, discord_configured, email_configured]):
        print("[WARNING] No alert channels configured. To enable alerts:")
        print("   1. Copy .env.example to .env (if not already done)")
        print("   2. Add your webhook/email configuration")
        print("   3. Uncomment the relevant alert variables")
        print()


def test_manual_alert(model_name: str):
    """
    Manually trigger drift detection and send alerts for a specific model.

    Args:
        model_name: Name of the model to test
    """
    print("=" * 80)
    print(f"MANUAL DRIFT TEST: {model_name}")
    print("=" * 80)
    print()

    detector = DriftDetector(threshold_percent=5.0)
    result = detector.process_run(model_name)

    print(json.dumps(result, indent=2))
    print()

    if result.get("drift_detected"):
        alerts_sent = result.get("alerts_sent", {})
        print(f"Alerts sent: {sum(alerts_sent.values())}/{len(alerts_sent)}")
        for channel, sent in alerts_sent.items():
            status = "[SENT]" if sent else "[FAILED/NOT CONFIGURED]"
            print(f"  {channel}: {status}")
    else:
        print("No drift detected - alerts not triggered")

    print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific model with alerts
        model = sys.argv[1]
        test_manual_alert(model)
    else:
        # Test all models (no alerts)
        test_drift_detection()
        print()
        print("TIP: To test alerts for a specific model, run:")
        print("   python scripts/test_drift_alerts.py <model-name>")
        print()
        print("Example:")
        print("   python scripts/test_drift_alerts.py gpt-4o")
