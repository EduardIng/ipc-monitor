import json
import os
import random
from datetime import date

from phrases import load_phrases

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "status_cache.json")


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE) as f:
        return json.load(f)


def save_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_app_key(app):
    return f"{app['number']}/{app['type']}-{app['year']}"


def should_notify(cache, app_key, status):
    entry = cache.get(app_key, {})
    today = date.today().isoformat()
    status_lower = status.lower()

    APPROVED_KEYWORDS = ["approved", "schváleno", "povolen", "kladně"]
    is_approved = any(w in status_lower for w in APPROVED_KEYWORDS)
    is_processing = "zpracovává se" in status_lower

    if is_approved:
        prev_status_lower = entry.get("last_status", "").lower()
        was_approved = any(w in prev_status_lower for w in APPROVED_KEYWORDS)
        return not was_approved  # Only notify if wasn't previously in any approved state

    if is_processing:
        # Notify once per day
        return entry.get("last_notified_date") != today

    # Any other status — notify only if changed
    return entry.get("last_status") != status


def update_cache(cache, app_key, status):
    cache[app_key] = {
        "last_status": status,
        "last_notified_date": date.today().isoformat(),
    }


def get_next_phrase(data):
    """Return next phrase using shuffle-bag: no repeats until all 41 used."""
    phrases = load_phrases()
    pool = data.get("phrases_pool", [])
    if not pool:
        pool = list(range(len(phrases)))
        random.shuffle(pool)
    idx = pool.pop(0)
    data["phrases_pool"] = pool
    return phrases[idx]
