# ~/ipc-monitor/adhoc.py
"""
Single-shot ad hoc check — always sends results regardless of notification history.
Mirrors bot.py _ad_hoc_check(). Run by GitHub Actions bot.yml on manual Telegram trigger.
"""
from __future__ import annotations
import logging
import sys

import config
from cache import get_app_key, get_next_phrase, load_cache, save_cache
from monitor import check_with_retry
from notifier import build_message, send_error, send_telegram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main():
    send_telegram("🔄 Перевіряю зараз...")
    data = load_cache()

    for app in config.APPLICATIONS:
        key = get_app_key(app)
        logger.info(f"Ad hoc check for {key}")
        status = check_with_retry(app)

        if status is None:
            send_error()
            continue

        phrase = get_next_phrase(data)
        msg = build_message(app, status, phrase)
        send_telegram(msg)
        logger.info(f"Ad hoc result sent for {key}")

    save_cache(data)


if __name__ == "__main__":
    main()
