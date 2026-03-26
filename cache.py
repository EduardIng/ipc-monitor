import json
import os
from datetime import date

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

    is_approved = any(w in status_lower for w in ["approved", "schváleno", "povolen"])
    is_processing = "zpracovává se" in status_lower

    if is_approved:
        # Notify only if status changed (i.e. wasn't already approved)
        return entry.get("last_status", "").lower() != status_lower

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
