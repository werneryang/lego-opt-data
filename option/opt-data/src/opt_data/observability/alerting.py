"""
Alerting system for opt-data.
"""

import logging
import requests
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages alerts and notifications.
    """

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url
        self._last_alert_time = {}  # key -> datetime
        self._cooldown = timedelta(minutes=5)  # Prevent spam

    def send_alert(self, title: str, message: str, level: str = "error", key: Optional[str] = None):
        """
        Send an alert.

        Args:
            title: Alert title
            message: Detailed message
            level: error, warning, info
            key: Dedup key for cooldown. If None, uses title.
        """
        dedup_key = key or title
        now = datetime.now()

        # Check cooldown
        if dedup_key in self._last_alert_time:
            if now - self._last_alert_time[dedup_key] < self._cooldown:
                logger.info(f"Suppressed alert '{title}' due to cooldown")
                return

        # Log it locally
        log_msg = f"ALERT [{level.upper()}]: {title} - {message}"
        if level == "error":
            logger.error(log_msg)
        elif level == "warning":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        # Send webhook if configured
        if self.webhook_url:
            self._send_webhook(title, message, level)

        self._last_alert_time[dedup_key] = now

    def _send_webhook(self, title: str, message: str, level: str):
        """Send to Slack/Discord compatible webhook."""
        try:
            color = (
                "#FF0000" if level == "error" else "#FFA500" if level == "warning" else "#00FF00"
            )
            payload = {
                "username": "Opt-Data Bot",
                "embeds": [
                    {
                        "title": title,
                        "description": message,
                        "color": int(color.replace("#", ""), 16),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ],
            }
            # Fallback for simple Slack hooks that don't support embeds
            if "slack.com" in self.webhook_url:
                payload = {"text": f"*{title}*\n{message}"}

            requests.post(self.webhook_url, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
