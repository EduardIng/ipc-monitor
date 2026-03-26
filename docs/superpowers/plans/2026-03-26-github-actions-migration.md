# GitHub Actions Migration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the IPC visa monitor from local launchd to GitHub Actions so it runs 24/7 even when the laptop is off, at zero cost.

**Architecture:** GitHub Actions cron workflow triggers `python monitor.py` on a Ubuntu runner 4×/day. Secrets (Telegram token, chat ID, application data) are stored in GitHub Actions Secrets. `status_cache.json` persists between runs via GitHub Actions Cache.

**Tech Stack:** Python 3.11, Playwright, GitHub Actions, `gh` CLI (for repo creation)

**Spec:** `docs/superpowers/specs/2026-03-26-github-actions-migration-design.md`

---

## Chunk 1: Code Changes

### Task 1: Add test fixtures for env-var-based config

**Files:**
- Create: `tests/conftest.py`

The `config.py` rewrite will read from `os.environ` at import time. Without env vars set, importing `config` in any test will raise `KeyError`. `conftest.py` sets safe test values before any test module is imported.

- [ ] **Step 1: Create `tests/conftest.py`**

```python
import os
import pytest

# Set env vars before any test module imports config
os.environ.setdefault("BOT_TOKEN", "test_token")
os.environ.setdefault("CHAT_ID", "123456")
os.environ.setdefault("APP_TRV", "35015,TP,2025")
os.environ.setdefault("APP_WRK", "18953,ZM,2026")
```

- [ ] **Step 2: Run existing tests to confirm they still pass**

```bash
cd ~/ipc-monitor && source venv/bin/activate && pytest tests/ -v
```

Expected: all existing tests pass (conftest only adds env vars, changes nothing yet).

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add conftest to set env vars before config import"
```

---

### Task 2: Rewrite config.py to read from environment variables

**Files:**
- Modify: `config.py`
- Create: `tests/test_config.py`

`config.py` currently hardcodes all values. Rewrite it to read from env vars. The `_parse_app` helper splits `"35015,TP,2025"` into the dict that the rest of the codebase expects, with an added `alias` field.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import os
import pytest


def test_parse_app_trv(monkeypatch):
    monkeypatch.setenv("APP_TRV", "35015,TP,2025")
    import importlib, config
    importlib.reload(config)
    app = config._parse_app("APP_TRV", "TRV")
    assert app == {"number": "35015", "type": "TP", "year": "2025", "alias": "TRV"}


def test_parse_app_wrk(monkeypatch):
    monkeypatch.setenv("APP_WRK", "18953,ZM,2026")
    import importlib, config
    importlib.reload(config)
    app = config._parse_app("APP_WRK", "WRK")
    assert app == {"number": "18953", "type": "ZM", "year": "2026", "alias": "WRK"}


def test_applications_list_has_two_entries():
    import importlib, config
    importlib.reload(config)
    assert len(config.APPLICATIONS) == 2
    aliases = [a["alias"] for a in config.APPLICATIONS]
    assert "TRV" in aliases
    assert "WRK" in aliases


def test_bot_token_from_env(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "my_secret_token")
    import importlib, config
    importlib.reload(config)
    assert config.BOT_TOKEN == "my_secret_token"


def test_chat_id_from_env(monkeypatch):
    monkeypatch.setenv("CHAT_ID", "999")
    import importlib, config
    importlib.reload(config)
    assert config.CHAT_ID == "999"


def test_missing_bot_token_raises(monkeypatch):
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    import importlib, config
    with pytest.raises(KeyError):
        importlib.reload(config)
```

- [ ] **Step 2: Run the test to confirm it fails**

```bash
pytest tests/test_config.py -v
```

Expected: FAIL — `_parse_app` not defined yet, `config.py` still has hardcoded values.

- [ ] **Step 3: Rewrite `config.py`**

> **Note:** `CHECK_HOURS` (previously defined here) is dropped — confirmed by grep that it is not imported anywhere else in the codebase. `TIMEZONE` is kept because `scraper.py` may depend on it indirectly via pytz.

```python
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
TIMEZONE = "Europe/Prague"


def _parse_app(env_var, alias):
    number, typ, year = os.environ[env_var].split(",")
    return {"number": number, "type": typ, "year": year, "alias": alias}


APPLICATIONS = [
    _parse_app("APP_TRV", "TRV"),
    _parse_app("APP_WRK", "WRK"),
]
```

- [ ] **Step 4: Run the tests to confirm they pass**

```bash
pytest tests/test_config.py -v
```

Expected: all 6 tests pass.

- [ ] **Step 5: Run full test suite to confirm nothing broken**

```bash
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat: read config from environment variables"
```

---

### Task 3: Update notifier.py to use alias in messages

**Files:**
- Modify: `notifier.py`
- Modify: `tests/test_notifier.py`

`build_message()` currently builds the label as `{number}/{type}-{year}`. It should use `app["alias"]` instead, so messages show `TRV` or `WRK`.

- [ ] **Step 1: Update test fixtures and assertions in `tests/test_notifier.py`**

**Preserve the existing import block at the top of the file** (`import pytest`, `from unittest.mock import patch, MagicMock`, `import notifier`). Only replace lines 5–36: the two fixture dicts and the five `build_message` test functions. Leave `test_send_telegram_calls_api` and `test_send_error_sends_correct_message` exactly as-is.

```python
# Replace existing APP_TP and APP_ZM with alias-aware versions:
APP_TP = {"number": "35015", "type": "TP", "year": "2025", "alias": "TRV"}
APP_ZM = {"number": "18953", "type": "ZM", "year": "2026", "alias": "WRK"}


def test_build_message_processing():
    msg = notifier.build_message(APP_TP, "Vaše žádost se zpracovává se.")
    assert "🔴 Заявка TRV" in msg
    assert "покидьки" in msg


def test_build_message_approved_schvaleno():
    msg = notifier.build_message(APP_TP, "Žádost byla schváleno.")
    assert "🟢 Заявка TRV" in msg
    assert "Уроди" in msg


def test_build_message_approved_povolen():
    msg = notifier.build_message(APP_ZM, "Pobyt povolen.")
    assert "🟢 Заявка WRK" in msg
    assert "Уроди" in msg


def test_build_message_approved_english():
    msg = notifier.build_message(APP_TP, "Application approved.")
    assert "🟢 Заявка TRV" in msg


def test_build_message_other_status():
    msg = notifier.build_message(APP_TP, "Žádost zamítnuta.")
    assert "⚠️ Заявка TRV" in msg
    assert "Žádost zamítnuta." in msg
    assert "Перевір сайт вручну!" in msg
```

(Leave `test_send_telegram_calls_api` and `test_send_error_sends_correct_message` unchanged.)

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
pytest tests/test_notifier.py -v
```

Expected: FAIL — `build_message` still uses `{number}/{type}-{year}`.

- [ ] **Step 3: Update `build_message()` in `notifier.py`**

Change only the label line at the top of `build_message`:

```python
def build_message(app, status, phrase=None):
    label = app["alias"]
    s = status.lower()

    is_approved = any(w in s for w in ["approved", "schváleno", "povolen", "kladně"])
    is_processing = "zpracovává se" in s

    if is_processing:
        text = phrase or "Ці покидьки досі пердять в лужу на твої податки, в морду б дав чесслово"
        return f"🔴 Заявка {label}\n{text}"
    if is_approved:
        return (
            f"🟢 Заявка {label}\n"
            f"Уроди доперли шо чехія без тебе загнеться, зачекай три дні а потім дзвони шоб знали хто тут батя"
        )
    return (
        f"⚠️ Заявка {label}\n"
        f"Новий статус: {status}\n"
        f"Перевір сайт вручну!"
    )
```

- [ ] **Step 4: Run the tests to confirm they pass**

```bash
pytest tests/test_notifier.py -v
```

Expected: all 7 tests pass.

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add notifier.py tests/test_notifier.py
git commit -m "feat: use application alias (TRV/WRK) in Telegram messages"
```

---

### Task 4: Remove file logging from monitor.py

**Files:**
- Modify: `monitor.py`

Cloud/CI environments capture stdout. Writing to a log file in a stateless runner is pointless (file disappears after the job). Remove the `FileHandler`; keep only `StreamHandler`.

- [ ] **Step 1: Update logging setup in `monitor.py`**

Replace the `logging.basicConfig(...)` block (lines 17–25) with:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
```

Also remove the `LOG_FILE` line above it (line 15). It is safe to delete: `LOG_FILE` is only referenced in the `FileHandler(LOG_FILE, ...)` call being removed — nowhere else in the file.

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass (monitor.py isn't tested directly, but nothing should break).

- [ ] **Step 3: Commit**

```bash
git add monitor.py
git commit -m "feat: log to stdout only (removes local file handler)"
```

---

## Chunk 2: GitHub Actions Workflow + Repo

### Task 5: Create the GitHub Actions workflow

**Files:**
- Create: `.github/workflows/monitor.yml`

The workflow runs on a cron schedule and on manual dispatch (`workflow_dispatch`). It restores the cache before running and saves it after, so `status_cache.json` persists between runs.

- [ ] **Step 1: Create `.github/workflows/monitor.yml`**

```yaml
name: IPC Monitor

on:
  schedule:
    - cron: "0 7,10,13,16 * * *"
  workflow_dispatch:

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/cache@v4
        with:
          path: status_cache.json
          # Static key is intentional: cache is never invalidated automatically.
          # This ensures status_cache.json persists indefinitely across runs.
          key: status-cache
          restore-keys: status-cache

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium --with-deps

      - name: Run monitor
        env:
          BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
          CHAT_ID: ${{ secrets.CHAT_ID }}
          APP_TRV: ${{ secrets.APP_TRV }}
          APP_WRK: ${{ secrets.APP_WRK }}
        run: python monitor.py
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/monitor.yml
git commit -m "feat: add GitHub Actions workflow for scheduled monitoring"
```

---

### Task 6: Create GitHub repo and push

**Files:** none — repo creation and push

- [ ] **Step 1: Create the public GitHub repo**

```bash
gh repo create EduardIng/ipc-monitor --public --source=. --remote=origin --push
```

Expected output: repo URL printed, all commits pushed to `origin/main`.

> **Note:** Secrets are configured in Task 7 (after this push). GitHub Actions `schedule` and `workflow_dispatch` triggers do not fire on push, so no run will be queued between this step and Task 7. The first run only happens when manually triggered in Task 8.

- [ ] **Step 2: Verify repo is live**

```bash
gh repo view EduardIng/ipc-monitor
```

Expected: repo details shown, visibility = public.

---

### Task 7: Configure GitHub Actions Secrets

Secret values are **not stored in this file** (public repo). Retrieve them from your local secure storage.

- [ ] **Step 1: Add all four secrets**

```bash
gh secret set BOT_TOKEN --body "<BOT_TOKEN>" --repo EduardIng/ipc-monitor
gh secret set CHAT_ID --body "<CHAT_ID>" --repo EduardIng/ipc-monitor
gh secret set APP_TRV --body "35015,TP,2025" --repo EduardIng/ipc-monitor
gh secret set APP_WRK --body "18953,ZM,2026" --repo EduardIng/ipc-monitor
```

Replace `<BOT_TOKEN>` and `<CHAT_ID>` with the actual values from your local secure storage. `APP_TRV` and `APP_WRK` are non-sensitive application reference numbers and safe to include as-is.

Expected: each command prints `✓ Set secret BOT_TOKEN for EduardIng/ipc-monitor` (etc.)

- [ ] **Step 2: Confirm all four secrets appear in repo settings**

```bash
gh secret list --repo EduardIng/ipc-monitor
```

Expected: 4 secrets listed — `APP_TRV`, `APP_WRK`, `BOT_TOKEN`, `CHAT_ID`.

---

### Task 8: Trigger a manual run and verify

- [ ] **Step 1: Trigger the workflow manually**

```bash
gh workflow run monitor.yml --repo EduardIng/ipc-monitor
```

Expected: `✓ Created workflow dispatch event`

- [ ] **Step 2: Watch the run complete**

```bash
gh run watch --repo EduardIng/ipc-monitor
```

Expected: run completes with green checkmark. Each step shows pass.

- [ ] **Step 3: Confirm Telegram message was received**

Check Telegram. You should receive a notification for TRV and/or WRK (depending on current status and what's in the cache on first run).

- [ ] **Step 4: View the raw run log to confirm correct execution**

```bash
gh run view --log --repo EduardIng/ipc-monitor
```

Look for lines like `IPC Monitor check started` and `IPC Monitor check completed` in the output. If the run failed, the log will show the exact error (import failure, missing env var, site error, etc.).

- [ ] **Step 5: Trigger a second manual run to verify cache works**

```bash
gh workflow run monitor.yml --repo EduardIng/ipc-monitor
gh run watch --repo EduardIng/ipc-monitor
```

Expected — depends on status returned by the site:

- **If status is "zpracovává se"**: no second Telegram notification (cache suppresses same-day duplicates). Confirmed by silence in Telegram.
- **If status is approved**: no second notification (cache records approval, won't repeat). Silence in Telegram.
- **If status is something else (other status)**: no notification if unchanged since run 1. Check the run log (`gh run view --log`) and confirm `No notification needed` appears for both applications.

In all cases: the second run must complete without error. Cache working correctly means the second run reads `status_cache.json` from the previous run (you can confirm by checking that the log does not show "first run" empty-cache behavior for both apps).
