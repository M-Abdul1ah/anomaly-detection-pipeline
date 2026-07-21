"""
PHASE 8 (SUPPORTING) — TELEGRAM NOTIFICATIONS

Sends a Telegram message whenever a Critical alert fires. Kept as its own
module (rather than inline in response.py) so the notification channel
could later be swapped/extended (email, Slack, etc.) without touching the
response routing logic itself.

Reads the bot token and chat ID from environment variables (loaded from a
local .env file, which is gitignored — never hardcode secrets here).

Fails quietly: if the token/chat ID are missing, or the network call
fails, this prints a warning and lets the pipeline keep running. A
notification failure should never take down the anomaly detector.
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_critical_alert(row) -> None:
    """Send one Telegram message for a single Critical alert row.
    `row` is a pandas Series with at least 'service' and 'anomaly_score'.
    """
    if not _BOT_TOKEN or not _CHAT_ID:
        print("[notifications] TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set "
              "in .env — skipping Telegram alert")
        return

    service = row.get("service", "unknown")
    score = row.get("anomaly_score", 0.0)

    message = (
        f"🚨 CRITICAL anomaly detected\n"
        f"Service: {service}\n"
        f"Anomaly score: {score:.3f}"
    )

    url = f"https://api.telegram.org/bot{_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": _CHAT_ID, "text": message}

    try:
        resp = requests.post(url, data=payload, timeout=5)
        if resp.status_code == 200:
            print(f"[notifications] Telegram alert sent for service={service}")
        else:
            print(f"[notifications] Telegram API returned "
                  f"{resp.status_code}: {resp.text}")
    except requests.RequestException as exc:
        print(f"[notifications] failed to send Telegram alert: {exc}")