"""
Drift detection and alerting system for the Eval Dashboard.
Sends alerts via HTTP webhooks, Discord, and Email when model accuracy drops.
"""
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Optional, List
import requests
from core.db import get_drift_analysis, Run


class DriftDetector:
    """
    Monitors model performance and sends alerts when drift is detected.
    """

    def __init__(self, threshold_percent: float = 5.0):
        """
        Initialize drift detector with configuration from environment.

        Args:
            threshold_percent: Accuracy drop percentage threshold (default 5%)
        """
        self.threshold = threshold_percent / 100.0  # Convert to decimal

        # Generic webhook configuration
        self.webhook_url = os.getenv("WEBHOOK_URL")

        # Discord configuration
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

        # Email configuration
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.alert_email_to = os.getenv("ALERT_EMAIL_TO")

    def check_drift(self, model_name: str, run_id: Optional[int] = None) -> Dict:
        """
        Check if a model has drifted and prepare alert payload.

        Args:
            model_name: Name of the model to check
            run_id: Optional specific run ID to check (uses latest if None)

        Returns:
            Dictionary with drift status and metrics
        """
        latest_run, best_run, has_drifted = get_drift_analysis(model_name, self.threshold)

        if not latest_run:
            return {
                "model": model_name,
                "drift_detected": False,
                "error": "No runs found for this model"
            }

        accuracy_drop = best_run.accuracy - latest_run.accuracy if best_run else 0.0
        drift_percentage = (accuracy_drop * 100) if best_run else 0.0

        return {
            "model": model_name,
            "drift_detected": has_drifted,
            "latest_run": {
                "id": latest_run.id,
                "accuracy": round(latest_run.accuracy * 100, 2),
                "timestamp": latest_run.timestamp.isoformat(),
                "cost": round(latest_run.total_cost, 4),
                "latency": round(latest_run.avg_latency, 2)
            },
            "best_run": {
                "id": best_run.id,
                "accuracy": round(best_run.accuracy * 100, 2),
                "timestamp": best_run.timestamp.isoformat()
            } if best_run else None,
            "drift_percentage": round(drift_percentage, 2),
            "threshold_percent": round(self.threshold * 100, 1),
            "timestamp": datetime.utcnow().isoformat()
        }

    def send_generic_webhook(self, payload: Dict) -> bool:
        """
        Send alert to generic HTTP webhook.

        Args:
            payload: Drift detection payload

        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            return False

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            print(f"[OK] Generic webhook alert sent to {self.webhook_url}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to send generic webhook: {e}")
            return False

    def send_discord_alert(self, payload: Dict) -> bool:
        """
        Send alert to Discord via webhook.

        Args:
            payload: Drift detection payload

        Returns:
            True if successful, False otherwise
        """
        if not self.discord_webhook_url:
            return False

        try:
            drift_detected = payload.get("drift_detected", False)
            model = payload.get("model", "Unknown")
            latest = payload.get("latest_run", {})
            best = payload.get("best_run", {})
            drift_pct = payload.get("drift_percentage", 0)

            # Determine embed color (red for drift, green for healthy)
            color = 0xFF0000 if drift_detected else 0x00FF00

            # Build embed
            embed = {
                "title": f"🚨 Model Drift Alert: {model}" if drift_detected else f"✅ Model Healthy: {model}",
                "description": (
                    f"**Accuracy dropped by {drift_pct}%**\n"
                    f"Current: {latest.get('accuracy', 0)}% → Best: {best.get('accuracy', 0) if best else 'N/A'}%"
                ) if drift_detected else f"Model performing within acceptable range",
                "color": color,
                "fields": [
                    {
                        "name": "Latest Accuracy",
                        "value": f"{latest.get('accuracy', 0)}%",
                        "inline": True
                    },
                    {
                        "name": "Best Accuracy",
                        "value": f"{best.get('accuracy', 0) if best else 'N/A'}%",
                        "inline": True
                    },
                    {
                        "name": "Drift",
                        "value": f"{drift_pct}%",
                        "inline": True
                    },
                    {
                        "name": "Avg Latency",
                        "value": f"{latest.get('latency', 0)}s",
                        "inline": True
                    },
                    {
                        "name": "Cost",
                        "value": f"${latest.get('cost', 0)}",
                        "inline": True
                    },
                    {
                        "name": "Run ID",
                        "value": f"#{latest.get('id', 0)}",
                        "inline": True
                    }
                ],
                "timestamp": payload.get("timestamp"),
                "footer": {
                    "text": "Eval Dashboard • Drift Detection"
                }
            }

            discord_payload = {
                "embeds": [embed]
            }

            response = requests.post(
                self.discord_webhook_url,
                json=discord_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            print(f"[OK] Discord alert sent")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to send Discord alert: {e}")
            return False

    def send_email_alert(self, payload: Dict) -> bool:
        """
        Send alert via email (SMTP).

        Args:
            payload: Drift detection payload

        Returns:
            True if successful, False otherwise
        """
        if not all([self.smtp_user, self.smtp_password, self.alert_email_to]):
            return False

        try:
            drift_detected = payload.get("drift_detected", False)
            model = payload.get("model", "Unknown")
            latest = payload.get("latest_run", {})
            best = payload.get("best_run", {})
            drift_pct = payload.get("drift_percentage", 0)

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚨 Model Drift Alert: {model}" if drift_detected else f"✅ Model Healthy: {model}"
            msg["From"] = self.smtp_user
            msg["To"] = self.alert_email_to

            # HTML email body
            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                  <h2 style="color: {'#d32f2f' if drift_detected else '#388e3c'};">
                    {'🚨 Model Drift Detected' if drift_detected else '✅ Model Performance Healthy'}
                  </h2>

                  <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Model: {model}</h3>
                    <p><strong>Status:</strong> {'⚠️ Drift Detected' if drift_detected else '✓ Within Threshold'}</p>
                    <p><strong>Accuracy Drop:</strong> {drift_pct}%</p>
                  </div>

                  <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background-color: #e0e0e0;">
                      <th style="padding: 10px; text-align: left; border: 1px solid #ccc;">Metric</th>
                      <th style="padding: 10px; text-align: left; border: 1px solid #ccc;">Latest Run</th>
                      <th style="padding: 10px; text-align: left; border: 1px solid #ccc;">Best Run</th>
                    </tr>
                    <tr>
                      <td style="padding: 10px; border: 1px solid #ccc;">Accuracy</td>
                      <td style="padding: 10px; border: 1px solid #ccc;">{latest.get('accuracy', 0)}%</td>
                      <td style="padding: 10px; border: 1px solid #ccc;">{best.get('accuracy', 0) if best else 'N/A'}%</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                      <td style="padding: 10px; border: 1px solid #ccc;">Run ID</td>
                      <td style="padding: 10px; border: 1px solid #ccc;">#{latest.get('id', 0)}</td>
                      <td style="padding: 10px; border: 1px solid #ccc;">#{best.get('id', 0) if best else 'N/A'}</td>
                    </tr>
                    <tr>
                      <td style="padding: 10px; border: 1px solid #ccc;">Avg Latency</td>
                      <td style="padding: 10px; border: 1px solid #ccc;">{latest.get('latency', 0)}s</td>
                      <td style="padding: 10px; border: 1px solid #ccc;">-</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                      <td style="padding: 10px; border: 1px solid #ccc;">Cost</td>
                      <td style="padding: 10px; border: 1px solid #ccc;">${latest.get('cost', 0)}</td>
                      <td style="padding: 10px; border: 1px solid #ccc;">-</td>
                    </tr>
                  </table>

                  {'<div style="background-color: #ffebee; padding: 15px; border-left: 4px solid #d32f2f; margin: 20px 0;"><h4 style="margin-top: 0;">⚠️ Action Required</h4><ul><li>Review recent model changes</li><li>Check for data quality issues</li><li>Investigate prompt modifications</li><li>Consider rolling back to previous version</li></ul></div>' if drift_detected else ''}

                  <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    Generated by Eval Dashboard • {payload.get('timestamp')}
                  </p>
                </div>
              </body>
            </html>
            """

            # Attach HTML content
            msg.attach(MIMEText(html, "html"))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            print(f"[OK] Email alert sent to {self.alert_email_to}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to send email alert: {e}")
            return False

    def send_all_alerts(self, payload: Dict) -> Dict[str, bool]:
        """
        Send alerts to all configured channels.

        Args:
            payload: Drift detection payload

        Returns:
            Dictionary of channel names to success status
        """
        results = {
            "webhook": self.send_generic_webhook(payload),
            "discord": self.send_discord_alert(payload),
            "email": self.send_email_alert(payload)
        }

        successful = sum(results.values())
        print(f"[INFO] Alerts sent: {successful}/{len(results)} channels")

        return results

    def process_run(self, model_name: str, run_id: Optional[int] = None) -> Dict:
        """
        Check drift for a model and send alerts if configured.

        Args:
            model_name: Name of the model to check
            run_id: Optional specific run ID

        Returns:
            Full result including drift status and alert results
        """
        # Check for drift
        drift_payload = self.check_drift(model_name, run_id)

        # Only send alerts if drift is detected
        alert_results = {}
        if drift_payload.get("drift_detected", False):
            print(f"[ALERT] Drift detected for {model_name}!")
            alert_results = self.send_all_alerts(drift_payload)
        else:
            print(f"[OK] No drift detected for {model_name}")

        return {
            **drift_payload,
            "alerts_sent": alert_results
        }


def check_model_drift(model_name: str, threshold_percent: float = 5.0) -> Dict:
    """
    Convenience function to check drift for a single model.

    Args:
        model_name: Model to check
        threshold_percent: Accuracy drop threshold (default 5%)

    Returns:
        Drift detection result with alert status
    """
    detector = DriftDetector(threshold_percent=threshold_percent)
    return detector.process_run(model_name)


if __name__ == "__main__":
    # Test drift detection
    import sys

    if len(sys.argv) > 1:
        model = sys.argv[1]
        result = check_model_drift(model)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python drift_detector.py <model_name>")
        print("Example: python drift_detector.py gpt-4o")
