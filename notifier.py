import logging
import requests
import config

logger = logging.getLogger(__name__)


def build_message(app, status, phrase=None):
    key = f"{app['number']}/{app['type']}-{app['year']}"
    s = status.lower()

    is_approved = any(w in s for w in ["approved", "schváleno", "povolen", "kladně"])
    is_processing = "zpracovává se" in s

    if is_processing:
        text = phrase or "Ці покидьки досі пердять в лужу на твої податки, в морду б дав чесслово"
        return f"🔴 Заявка {key}\n{text}"
    if is_approved:
        return (
            f"🟢 Заявка {key}\n"
            f"Уроди доперли шо чехія без тебе загнеться, зачекай три дні а потім дзвони шоб знали хто тут батя"
        )
    return (
        f"⚠️ Заявка {key}\n"
        f"Новий статус: {status}\n"
        f"Перевір сайт вручну!"
    )


def send_telegram(message):
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": config.CHAT_ID, "text": message})
    resp.raise_for_status()
    logger.info(f"Telegram sent: {message[:60]}…")


def send_error():
    send_telegram("❌ IPC Monitor: сайт недоступний, перевірка не вдалась")
