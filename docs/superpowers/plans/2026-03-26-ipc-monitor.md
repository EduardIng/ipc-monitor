# IPC Visa Monitor — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Monitor two Czech residence permit applications on ipc.gov.cz via Playwright and send Telegram notifications on status changes.

**Architecture:** Standalone Python script triggered 4×/day by macOS launchd. Modules: scraper (Playwright), notifier (Telegram), cache (JSON persistence), main orchestrator.

**Tech Stack:** Python 3.11+, Playwright (async, headless Chromium), requests, pytz, pytest

---

## File Map

| Path | Action | Purpose |
|------|--------|---------|
| `~/ipc-monitor/CLAUDE.md` | Create | Project reference (from spec) |
| `~/ipc-monitor/config.py` | Create | Tokens, applications, schedule |
| `~/ipc-monitor/cache.py` | Create | Read/write status_cache.json |
| `~/ipc-monitor/notifier.py` | Create | Build messages + send Telegram |
| `~/ipc-monitor/scraper.py` | Create | Playwright form interaction |
| `~/ipc-monitor/monitor.py` | Create | Main entry point, orchestration |
| `~/ipc-monitor/status_cache.json` | Create | Persisted state (empty init) |
| `~/ipc-monitor/requirements.txt` | Create | Python dependencies |
| `~/ipc-monitor/com.ipc.monitor.plist` | Create | launchd config |
| `~/ipc-monitor/install.sh` | Create | One-command setup |
| `~/ipc-monitor/tests/test_cache.py` | Create | Unit tests for cache logic |
| `~/ipc-monitor/tests/test_notifier.py` | Create | Unit tests for message building |

---

## Chunk 1: Project scaffold + config

### Task 1: Create project folder, CLAUDE.md, config.py, requirements.txt

**Files:**
- Create: `~/ipc-monitor/CLAUDE.md`
- Create: `~/ipc-monitor/config.py`
- Create: `~/ipc-monitor/requirements.txt`
- Create: `~/ipc-monitor/status_cache.json`
- Create: `~/ipc-monitor/tests/__init__.py`

- [ ] **Step 1: Create project directory and CLAUDE.md**

```bash
mkdir -p ~/ipc-monitor/tests
```

Create `~/ipc-monitor/CLAUDE.md`:

```markdown
# IPC Visa Monitor — Project Reference

Цей файл є головним референсом для всіх неоднозначних ситуацій в проекті.
При будь-яких сумнівах — читай цей файл першим.

## Мета проекту
Автоматичний моніторинг двох заявок на дозвіл проживання в Чехії на сайті ipc.gov.cz.
Сповіщення через Telegram бота.

## Заявки
- Заявка 1: номер 35015, тип TP, рік 2025
- Заявка 2: номер 18953, тип ZM, рік 2026

## Технічний стек
- Python 3.11+
- Playwright (headless Chromium) — НЕ requests/BeautifulSoup, сайт на Vue.js
- Telegram Bot API через requests
- launchd для розкладу на macOS
- Virtual environment: ~/ipc-monitor/venv/

## Розклад перевірок
08:00, 11:00, 14:00, 17:00 за Europe/Prague

## Логіка повідомлень
- "zpracovává se" → надсилати раз на день (перша перевірка дня)
- approved/schváleno/povolen → надіслати одразу, більше не повторювати
- будь-який інший статус → надіслати одразу з точним текстом
- сайт недоступний після 3 спроб → надіслати помилку

## Тексти повідомлень (не змінювати!)
В обробці:
🔴 Заявка {номер}/{тип}-{рік}
Ці покидьки досі пердять в лужу на твої податки, в морду б дав чесслово

Approved:
🟢 Заявка {номер}/{тип}-{рік}
Уроди доперли шо чехія без тебе загнеться, зачекай три дні а потім дзвони шоб знали хто тут батя

Інший статус:
⚠️ Заявка {номер}/{тип}-{рік}
Новий статус: {точний текст зі сторінки}
Перевір сайт вручну!

Недоступний:
❌ IPC Monitor: сайт недоступний, перевірка не вдалась

## Важливі технічні деталі
- Дропдауни на сайті кастомні (Vue компоненти) — клікати по тексту опції, НЕ по value
- page.wait_for_selector() замість time.sleep()
- Retry: 3 спроби з паузою 30 секунд
- Попередній статус зберігається в status_cache.json
- Всі шляхи в plist файлі мають бути абсолютними

## Структура файлів
~/ipc-monitor/
├── CLAUDE.md               ← цей файл
├── monitor.py              ← основний скрипт
├── config.py               ← токени і дані заявок
├── cache.py                ← логіка кешу
├── notifier.py             ← Telegram повідомлення
├── scraper.py              ← Playwright scraping
├── status_cache.json       ← кеш статусів
├── requirements.txt        ← залежності
├── com.ipc.monitor.plist   ← launchd конфіг
├── install.sh              ← встановлення одною командою
├── ipc_monitor.log         ← логи
└── tests/                  ← unit tests
```

- [ ] **Step 2: Create config.py**

```python
# ~/ipc-monitor/config.py
BOT_TOKEN = "ВСТАВИТИ_ПІСЛЯ_СТВОРЕННЯ_БОТА"
CHAT_ID = "ВСТАВИТИ_ПІСЛЯ_ОТРИМАННЯ"
TIMEZONE = "Europe/Prague"
CHECK_HOURS = [8, 11, 14, 17]

APPLICATIONS = [
    {"number": "35015", "type": "TP", "year": "2025"},
    {"number": "18953", "type": "ZM", "year": "2026"},
]
```

- [ ] **Step 3: Create requirements.txt**

```
playwright==1.42.0
requests==2.31.0
pytz==2024.1
pytest==8.1.0
```

- [ ] **Step 4: Create empty status_cache.json and tests/__init__.py**

`~/ipc-monitor/status_cache.json`:
```json
{}
```

`~/ipc-monitor/tests/__init__.py`:
```python
```

- [ ] **Step 5: No commit yet — wait for venv in install.sh**

---

## Chunk 2: Cache module

### Task 2: cache.py with tests

**Files:**
- Create: `~/ipc-monitor/cache.py`
- Create: `~/ipc-monitor/tests/test_cache.py`

- [ ] **Step 1: Write failing tests for cache logic**

Create `~/ipc-monitor/tests/test_cache.py`:

```python
import json
import os
import tempfile
from datetime import date, timedelta
import pytest

# We'll import cache after setting CACHE_FILE via monkeypatch
import cache


@pytest.fixture
def tmp_cache_file(tmp_path, monkeypatch):
    cache_file = tmp_path / "status_cache.json"
    monkeypatch.setattr(cache, "CACHE_FILE", str(cache_file))
    return cache_file


def test_load_cache_returns_empty_dict_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_FILE", str(tmp_path / "nonexistent.json"))
    result = cache.load_cache()
    assert result == {}


def test_save_and_load_roundtrip(tmp_cache_file):
    data = {"key": {"last_status": "processing", "last_notified_date": "2026-01-01"}}
    cache.save_cache(data)
    loaded = cache.load_cache()
    assert loaded == data


def test_get_app_key():
    app = {"number": "35015", "type": "TP", "year": "2025"}
    assert cache.get_app_key(app) == "35015/TP-2025"


def test_should_notify_processing_first_time():
    c = {}
    assert cache.should_notify(c, "35015/TP-2025", "zpracovává se") is True


def test_should_notify_processing_same_day_returns_false():
    today = date.today().isoformat()
    c = {"35015/TP-2025": {"last_status": "zpracovává se", "last_notified_date": today}}
    assert cache.should_notify(c, "35015/TP-2025", "zpracovává se") is False


def test_should_notify_processing_new_day_returns_true():
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    c = {"35015/TP-2025": {"last_status": "zpracovává se", "last_notified_date": yesterday}}
    assert cache.should_notify(c, "35015/TP-2025", "zpracovává se") is True


def test_should_notify_approved_first_time():
    c = {}
    assert cache.should_notify(c, "35015/TP-2025", "schváleno") is True


def test_should_notify_approved_already_notified():
    c = {"35015/TP-2025": {"last_status": "schváleno", "last_notified_date": "2026-01-01"}}
    assert cache.should_notify(c, "35015/TP-2025", "schváleno") is False


def test_should_notify_other_status_new():
    c = {}
    assert cache.should_notify(c, "35015/TP-2025", "nějaký jiný stav") is True


def test_should_notify_other_status_unchanged():
    c = {"35015/TP-2025": {"last_status": "nějaký jiný stav", "last_notified_date": "2026-01-01"}}
    assert cache.should_notify(c, "35015/TP-2025", "nějaký jiný stav") is False


def test_update_cache_sets_today():
    c = {}
    cache.update_cache(c, "35015/TP-2025", "zpracovává se")
    assert c["35015/TP-2025"]["last_status"] == "zpracovává se"
    assert c["35015/TP-2025"]["last_notified_date"] == date.today().isoformat()
```

- [ ] **Step 2: Run tests — expect failure (module not found)**

```bash
cd ~/ipc-monitor && venv/bin/pytest tests/test_cache.py -v
```

Expected: `ModuleNotFoundError: No module named 'cache'`

- [ ] **Step 3: Create cache.py**

```python
# ~/ipc-monitor/cache.py
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
```

- [ ] **Step 4: Run tests — expect all pass**

```bash
cd ~/ipc-monitor && venv/bin/pytest tests/test_cache.py -v
```

Expected: all 10 tests PASS

---

## Chunk 3: Notifier module

### Task 3: notifier.py with tests

**Files:**
- Create: `~/ipc-monitor/notifier.py`
- Create: `~/ipc-monitor/tests/test_notifier.py`

- [ ] **Step 1: Write failing tests for message building**

Create `~/ipc-monitor/tests/test_notifier.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
import notifier

APP_TP = {"number": "35015", "type": "TP", "year": "2025"}
APP_ZM = {"number": "18953", "type": "ZM", "year": "2026"}


def test_build_message_processing():
    msg = notifier.build_message(APP_TP, "Vaše žádost se zpracovává se.")
    assert "🔴 Заявка 35015/TP-2025" in msg
    assert "покидьки" in msg


def test_build_message_approved_schvaleno():
    msg = notifier.build_message(APP_TP, "Žádost byla schváleno.")
    assert "🟢 Заявка 35015/TP-2025" in msg
    assert "Уроди" in msg


def test_build_message_approved_povolen():
    msg = notifier.build_message(APP_ZM, "Pobyt povolen.")
    assert "🟢 Заявка 18953/ZM-2026" in msg
    assert "Уроди" in msg


def test_build_message_approved_english():
    msg = notifier.build_message(APP_TP, "Application approved.")
    assert "🟢 Заявка 35015/TP-2025" in msg


def test_build_message_other_status():
    msg = notifier.build_message(APP_TP, "Žádost zamítnuta.")
    assert "⚠️ Заявка 35015/TP-2025" in msg
    assert "Žádost zamítnuta." in msg
    assert "Перевір сайт вручну!" in msg


def test_send_telegram_calls_api(monkeypatch):
    mock_post = MagicMock()
    mock_post.return_value.raise_for_status = MagicMock()
    monkeypatch.setattr("notifier.requests.post", mock_post)
    monkeypatch.setattr("notifier.config.BOT_TOKEN", "test_token")
    monkeypatch.setattr("notifier.config.CHAT_ID", "12345")

    notifier.send_telegram("hello")

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert "test_token" in call_kwargs[0][0]
    assert call_kwargs[1]["json"]["text"] == "hello"
    assert call_kwargs[1]["json"]["chat_id"] == "12345"


def test_send_error_sends_correct_message(monkeypatch):
    sent = []
    monkeypatch.setattr("notifier.send_telegram", lambda msg: sent.append(msg))
    notifier.send_error()
    assert len(sent) == 1
    assert "❌ IPC Monitor" in sent[0]
    assert "недоступний" in sent[0]
```

- [ ] **Step 2: Run tests — expect failure**

```bash
cd ~/ipc-monitor && venv/bin/pytest tests/test_notifier.py -v
```

Expected: `ModuleNotFoundError: No module named 'notifier'`

- [ ] **Step 3: Create notifier.py**

```python
# ~/ipc-monitor/notifier.py
import logging
import requests
import config

logger = logging.getLogger(__name__)


def build_message(app, status):
    key = f"{app['number']}/{app['type']}-{app['year']}"
    s = status.lower()

    is_approved = any(w in s for w in ["approved", "schváleno", "povolen"])
    is_processing = "zpracovává se" in s

    if is_processing:
        return (
            f"🔴 Заявка {key}\n"
            f"Ці покидьки досі пердять в лужу на твої податки, в морду б дав чесслово"
        )
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
```

- [ ] **Step 4: Run tests — expect all pass**

```bash
cd ~/ipc-monitor && venv/bin/pytest tests/test_notifier.py -v
```

Expected: all 7 tests PASS

---

## Chunk 4: Scraper module

### Task 4: scraper.py (Playwright)

**Files:**
- Create: `~/ipc-monitor/scraper.py`

No unit tests for the scraper — it requires real network + browser. Integration tested in Task 7.

- [ ] **Step 1: Create scraper.py**

```python
# ~/ipc-monitor/scraper.py
"""
Playwright scraper for https://ipc.gov.cz/informace-o-stavu-rizeni/

The page uses Vue.js with custom dropdown components (likely vue-select).
Dropdowns are NOT native <select> — interact by clicking trigger, then
clicking the matching list item by its text content.

If selectors break after site updates, inspect the page with:
    chromium --headless=new --dump-dom https://ipc.gov.cz/informace-o-stavu-rizeni/
or run scraper.py with headless=False to watch the browser.
"""
import asyncio
import logging

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

logger = logging.getLogger(__name__)

URL = "https://ipc.gov.cz/informace-o-stavu-rizeni/"
TIMEOUT = 30_000  # ms


async def _fill_form_and_get_status(page, number: str, typ: str, year: str) -> str:
    await page.goto(URL, timeout=TIMEOUT)

    # --- Reference number ---
    await page.wait_for_selector('input[name="proceedings.referenceNumber"]', timeout=TIMEOUT)
    await page.fill('input[name="proceedings.referenceNumber"]', number)

    # --- Typ řízení dropdown ---
    # Vue-select: the visible trigger is a div with role="combobox" or class "vs__search"
    # Strategy: find the fieldset/div labelled "Typ řízení", click its dropdown trigger
    await _select_dropdown(page, label_text="Typ řízení", option_text=typ)

    # --- Rok dropdown ---
    await _select_dropdown(page, label_text="Rok", option_text=year)

    # --- Submit ---
    await page.click('button:has-text("Ověřit")')

    # --- Wait for result ---
    # The result appears in an .alert element or a div with role="alert"
    result_selector = '.alert, [role="alert"], .result-message, [class*="result"]'
    await page.wait_for_selector(result_selector, timeout=TIMEOUT)

    # Get all matching elements and return the most relevant text
    elements = await page.query_selector_all(result_selector)
    texts = []
    for el in elements:
        t = (await el.inner_text()).strip()
        if t:
            texts.append(t)

    return " | ".join(texts) if texts else ""


async def _select_dropdown(page, label_text: str, option_text: str):
    """
    Open a Vue-select dropdown identified by its nearby label text,
    then click the option matching option_text.
    """
    # Find the dropdown container near the label
    # Approach 1: label element with matching text → next sibling vue-select container
    # Approach 2: find any element containing the label text, then find .vs__dropdown-toggle nearby
    label = page.locator(f'label:has-text("{label_text}")')
    count = await label.count()

    if count > 0:
        # Click the dropdown toggle within the same form group as this label
        parent = label.locator("xpath=..")
        toggle = parent.locator(".vs__dropdown-toggle, [class*='dropdown-toggle'], [class*='select']").first
        await toggle.click()
    else:
        # Fallback: find any clickable element with the label text
        await page.click(f'text="{label_text}"')

    # Wait for options list to appear
    await page.wait_for_selector(
        ".vs__dropdown-menu, [class*='dropdown-menu'], [class*='dropdown-list']",
        timeout=TIMEOUT,
    )

    # Click the option matching the text
    option = page.locator(
        f".vs__dropdown-menu li:has-text('{option_text}'), "
        f"[class*='dropdown-menu'] li:has-text('{option_text}'), "
        f"[class*='dropdown-option']:has-text('{option_text}')"
    ).first
    await option.click()

    # Wait for dropdown to close
    await page.wait_for_selector(
        ".vs__dropdown-menu, [class*='dropdown-menu']",
        state="hidden",
        timeout=TIMEOUT,
    )


async def check_application(number: str, typ: str, year: str) -> str:
    """
    Returns the status text from the page, or raises an exception.
    Called once per application per check run.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()
        try:
            logger.debug(f"Checking {number}/{typ}-{year}")
            status = await _fill_form_and_get_status(page, number, typ, year)
            logger.debug(f"Got status: {status!r}")
            return status
        finally:
            await browser.close()
```

- [ ] **Step 2: Verify scraper.py is syntactically valid**

```bash
cd ~/ipc-monitor && venv/bin/python -c "import scraper; print('OK')"
```

Expected: `OK`

---

## Chunk 5: Main orchestrator

### Task 5: monitor.py

**Files:**
- Create: `~/ipc-monitor/monitor.py`

- [ ] **Step 1: Create monitor.py**

```python
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

    cache = load_cache()

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

        if should_notify(cache, key, status):
            msg = build_message(app, status)
            send_telegram(msg)
            logger.info(f"Notification sent for {key}")
            update_cache(cache, key, status)
        else:
            logger.info(f"No notification needed for {key} (already notified)")

    save_cache(cache)
    logger.info("IPC Monitor check completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify syntax**

```bash
cd ~/ipc-monitor && venv/bin/python -c "import monitor; print('OK')"
```

Expected: `OK`

---

## Chunk 6: launchd + install.sh

### Task 6: com.ipc.monitor.plist + install.sh

**Files:**
- Create: `~/ipc-monitor/com.ipc.monitor.plist`
- Create: `~/ipc-monitor/install.sh`

- [ ] **Step 1: Create com.ipc.monitor.plist**

Note: `StartCalendarInterval` uses the system's local clock. The `TZ` env var is set so Python's datetime is correct, but launchd itself ignores TZ. If your Mac is set to Europe/Prague timezone, the hours (8, 11, 14, 17) are correct as-is.

Replace `USERNAME` with the actual value from `echo $USER` (done dynamically by install.sh).

The plist template at `~/ipc-monitor/com.ipc.monitor.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ipc.monitor</string>

    <key>ProgramArguments</key>
    <array>
        <string>__VENV_PYTHON__</string>
        <string>__PROJECT_DIR__/monitor.py</string>
    </array>

    <key>StartCalendarInterval</key>
    <array>
        <dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>11</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>14</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>17</integer><key>Minute</key><integer>0</integer></dict>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>TZ</key>
        <string>Europe/Prague</string>
        <key>HOME</key>
        <string>__HOME__</string>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>

    <key>WorkingDirectory</key>
    <string>__PROJECT_DIR__</string>

    <key>StandardOutPath</key>
    <string>__PROJECT_DIR__/ipc_monitor.log</string>

    <key>StandardErrorPath</key>
    <string>__PROJECT_DIR__/ipc_monitor.log</string>

    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

- [ ] **Step 2: Create install.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$HOME/ipc-monitor"
VENV_DIR="$PROJECT_DIR/venv"
PLIST_NAME="com.ipc.monitor"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
FINAL_PLIST="$LAUNCH_AGENTS/$PLIST_NAME.plist"

echo "=== IPC Monitor Installer ==="
echo ""

# 1. Check Python 3.11+
PYTHON=$(command -v python3.11 || command -v python3 || true)
if [ -z "$PYTHON" ]; then
    echo "❌ Python 3.11+ not found. Install via: brew install python@3.11"
    exit 1
fi

PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]); then
    echo "❌ Python $PY_VER found, need 3.11+. Install via: brew install python@3.11"
    exit 1
fi
echo "✅ Python $PY_VER found at $PYTHON"

# 2. Create venv
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment…"
    "$PYTHON" -m venv "$VENV_DIR"
fi
echo "✅ Virtual environment: $VENV_DIR"

# 3. Install dependencies
echo "Installing Python packages…"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$PROJECT_DIR/requirements.txt"
echo "✅ Python packages installed"

# 4. Install Playwright Chromium
echo "Installing Playwright Chromium (this may take a minute)…"
"$VENV_DIR/bin/playwright" install chromium
echo "✅ Playwright Chromium installed"

# 5. Generate plist with real paths
mkdir -p "$LAUNCH_AGENTS"
VENV_PYTHON="$VENV_DIR/bin/python"

sed \
    -e "s|__VENV_PYTHON__|$VENV_PYTHON|g" \
    -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
    -e "s|__HOME__|$HOME|g" \
    "$PROJECT_DIR/com.ipc.monitor.plist" > "$FINAL_PLIST"

echo "✅ plist written to $FINAL_PLIST"

# 6. Register with launchd
if launchctl list | grep -q "$PLIST_NAME" 2>/dev/null; then
    echo "Unloading existing launchd job…"
    launchctl unload "$FINAL_PLIST" 2>/dev/null || true
fi
launchctl load "$FINAL_PLIST"
echo "✅ launchd job registered"

# 7. Done — manual test instructions
echo ""
echo "============================================="
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Open: $PROJECT_DIR/config.py"
echo "  2. Replace BOT_TOKEN and CHAT_ID with your Telegram values"
echo "  3. Run a test:  python $PROJECT_DIR/monitor.py"
echo ""
echo "Scheduled checks: 08:00, 11:00, 14:00, 17:00 (system local time)"
echo "⚠️  Make sure your Mac timezone is set to Europe/Prague"
echo "     (System Settings → General → Date & Time → Time Zone)"
echo "============================================="
```

- [ ] **Step 3: Make install.sh executable**

```bash
chmod +x ~/ipc-monitor/install.sh
```

---

## Chunk 7: Telegram bot instructions + integration test

### Task 7: Telegram setup guide + verify monitor runs

This task is interactive — you need the user to provide BOT_TOKEN and CHAT_ID.

- [ ] **Step 1: Show Telegram bot creation instructions**

Print to the user:

```
=== Як створити Telegram бота ===

1. Відкрий Telegram і знайди @BotFather
   (або перейди за посиланням: https://t.me/BotFather)

2. Напиши команду:
   /newbot

3. BotFather запитає ім'я бота (відображуване):
   Наприклад: IPC Monitor

4. Потім попросить username (має закінчуватись на 'bot'):
   Наприклад: my_ipc_monitor_bot

5. BotFather відповість з токеном — виглядає так:
   1234567890:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   Це твій BOT_TOKEN — збережи його!

6. Відкрий діалог зі своїм ботом і натисни START
   (або напиши будь-яке повідомлення — це активує чат)

7. Отримай свій CHAT_ID — відкрий у браузері:
   https://api.telegram.org/bot<ТВІЙ_TOKEN>/getUpdates

   У відповіді знайди:
   "chat":{"id": 123456789, ...}
   Число 123456789 — це твій CHAT_ID

Після отримання обох значень — встав їх в config.py:
   BOT_TOKEN = "1234567890:AAFxxx..."
   CHAT_ID = "123456789"

Потім запусти: python ~/ipc-monitor/monitor.py
```

- [ ] **Step 2: After user provides tokens — update config.py**

Open `~/ipc-monitor/config.py` and replace:
```python
BOT_TOKEN = "ВСТАВИТИ_ПІСЛЯ_СТВОРЕННЯ_БОТА"
CHAT_ID = "ВСТАВИТИ_ПІСЛЯ_ОТРИМАННЯ"
```
with the actual values.

- [ ] **Step 3: Run full integration test**

```bash
cd ~/ipc-monitor && venv/bin/python monitor.py
```

Expected output in terminal and `ipc_monitor.log`:
```
2026-03-26 HH:MM:SS INFO ============================================================
2026-03-26 HH:MM:SS INFO IPC Monitor check started
2026-03-26 HH:MM:SS INFO Checking 35015/TP-2025 (attempt 1/3)
2026-03-26 HH:MM:SS INFO Status for 35015/TP-2025: '...'
2026-03-26 HH:MM:SS INFO Notification sent for 35015/TP-2025
2026-03-26 HH:MM:SS INFO Checking 18953/ZM-2026 (attempt 1/3)
2026-03-26 HH:MM:SS INFO Status for 18953/ZM-2026: '...'
2026-03-26 HH:MM:SS INFO Notification sent for 18953/ZM-2026
2026-03-26 HH:MM:SS INFO IPC Monitor check completed
```

Expected: two Telegram messages arrive on your phone.

- [ ] **Step 4: If scraper fails — debug selectors**

If the scraper raises a `TimeoutError` or returns empty status, the Vue dropdown selectors may need adjustment. Debug with:

```bash
cd ~/ipc-monitor && venv/bin/python - <<'EOF'
import asyncio
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # visible window!
        page = await browser.new_page()
        await page.goto("https://ipc.gov.cz/informace-o-stavu-rizeni/")
        input("Press Enter to close browser...")
        await browser.close()

asyncio.run(debug())
EOF
```

This opens a visible browser window. Inspect the dropdown HTML in DevTools, then update the selectors in `scraper.py:_select_dropdown()`.

- [ ] **Step 5: Run full unit test suite**

```bash
cd ~/ipc-monitor && venv/bin/pytest tests/ -v
```

Expected: all tests PASS

---

## Final verification checklist

- [ ] `venv/bin/pytest tests/ -v` → all green
- [ ] `python monitor.py` → runs without error, Telegram messages received
- [ ] `cat ipc_monitor.log` → correct timestamps and status entries
- [ ] `launchctl list | grep ipc` → shows `com.ipc.monitor` as loaded
- [ ] Mac timezone set to Europe/Prague (System Settings → General → Date & Time)
