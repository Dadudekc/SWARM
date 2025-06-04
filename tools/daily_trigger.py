"""Daily trigger checks for Victor's self-discovery suite."""

import logging
import os
import time
from datetime import datetime
from typing import List

import requests
import schedule

from self_discovery.journal import get_today_stats, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

CHECK_TIME = os.getenv("CHECK_TIME", "18:00")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def send_notification(message: str) -> None:
    """Send a notification via Discord webhook or log to console."""
    if WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json={"content": message}, timeout=5)
        except Exception as exc:
            logging.error("Failed to send webhook: %s", exc)
    else:
        logging.info(message)


def check_activities() -> None:
    """Check today's activity status and send reminders if needed."""
    stats = get_today_stats()
    missing: List[str] = [name for name, done in (
        ("coding", stats["coded"]),
        ("trading", stats["traded"]),
        ("journaling", stats["journaled"]),
    ) if not done]

    if not missing:
        send_notification("Great work today! All activities logged.")
    else:
        send_notification(
            f"Reminder: you haven't completed {' ,'.join(missing)} today. Keep pushing!"
        )


def main() -> None:
    """Run the daily trigger scheduler."""
    init_db()
    schedule.every().day.at(CHECK_TIME).do(check_activities)
    logging.info("Daily trigger scheduled at %s", CHECK_TIME)
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
