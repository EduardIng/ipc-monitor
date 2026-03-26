# ~/ipc-monitor/bot.py
"""
Telegram bot long-polling listener.
Any message from CHAT_ID triggers an immediate ad hoc check of all applications.
Results are always sent regardless of whether status changed.
Runs persistently via launchd (KeepAlive = true).
"""
from __future__ import annotations
import logging
import os
import sys
import time

import requests

import config
from cache import get_app_key, get_next_phrase, load_cache, save_cache
from monitor import check_with_retry, LOG_FILE, RETRY_COUNT
from notifier import build_message, send_error, send_telegram

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


def _ad_hoc_check():
    """Run immediate check for all apps and always send results."""
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


def _get_initial_offset() -> int | None:
    """Skip updates that arrived before bot started."""
    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{config.BOT_TOKEN}/getUpdates",
            params={"timeout": 0},
            timeout=10,
        )
        updates = resp.json().get("result", [])
        if updates:
            return updates[-1]["update_id"] + 1
    except Exception as exc:
        logger.warning(f"Could not get initial offset: {exc}")
    return None


def poll():
    offset = _get_initial_offset()
    logger.info("Bot polling started — waiting for messages")

    while True:
        try:
            params: dict = {"timeout": 30, "allowed_updates": ["message"]}
            if offset is not None:
                params["offset"] = offset

            resp = requests.get(
                f"https://api.telegram.org/bot{config.BOT_TOKEN}/getUpdates",
                params=params,
                timeout=35,
            )
            resp.raise_for_status()

            for update in resp.json().get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message", {})
                chat_id = str(message.get("chat", {}).get("id", ""))
                if chat_id == str(config.CHAT_ID):
                    logger.info("Ad hoc check triggered via Telegram")
                    _ad_hoc_check()

        except Exception as exc:
            logger.error(f"Polling error: {exc}")
            time.sleep(5)


if __name__ == "__main__":
    poll()
