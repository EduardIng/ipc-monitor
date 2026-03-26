# ~/ipc-monitor/monitor.py
import asyncio
import logging
import os
import sys
import time

import config
from cache import get_app_key, load_cache, save_cache, should_notify, update_cache
from notifier import build_message, send_error, send_telegram
from scraper import check_application

# --- Logging setup ---
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ipc_monitor.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

RETRY_COUNT = 3
RETRY_PAUSE = 30  # seconds


def _check_with_retry(app) -> str | None:
    key = get_app_key(app)
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            logger.info(f"Checking {key} (attempt {attempt}/{RETRY_COUNT})")
            status = asyncio.run(
                check_application(app["number"], app["type"], app["year"])
            )
            logger.info(f"Status for {key}: {status!r}")
            return status
        except Exception as exc:
            logger.error(f"Attempt {attempt} failed for {key}: {exc}")
            if attempt < RETRY_COUNT:
                logger.info(f"Waiting {RETRY_PAUSE}s before retry…")
                time.sleep(RETRY_PAUSE)
    return None


def main():
    logger.info("=" * 60)
    logger.info("IPC Monitor check started")

    data = load_cache()

    for app in config.APPLICATIONS:
        key = get_app_key(app)
        status = _check_with_retry(app)

        if status is None:
            logger.error(f"All {RETRY_COUNT} attempts failed for {key} — sending error")
            send_error()
            continue

        if not status:
            logger.warning(f"Empty status returned for {key} — skipping")
            continue

        if should_notify(data, key, status):
            msg = build_message(app, status)
            send_telegram(msg)
            logger.info(f"Notification sent for {key}")
            update_cache(data, key, status)
        else:
            logger.info(f"No notification needed for {key} (already notified)")

    save_cache(data)
    logger.info("IPC Monitor check completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
