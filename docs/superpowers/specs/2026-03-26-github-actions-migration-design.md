# IPC Monitor — GitHub Actions Migration Design
**Date:** 2026-03-26
**Status:** Approved

## Goal

Move the IPC visa monitor off the local laptop so it runs 24/7 even when the machine is off. Chosen platform: GitHub Actions (public repo). Zero cost regardless of request volume.

---

## Architecture

```
GitHub repo: EduardIng/ipc-monitor (public)
│
├── .github/workflows/monitor.yml
│   └── cron: 0 7,10,13,16 * * *  (UTC)
│       = 08:00, 11:00, 14:00, 17:00 Prague (winter)
│       = 09:00, 12:00, 15:00, 18:00 Prague (summer, +1h DST drift — acceptable)
│
├── GitHub Actions Secrets (encrypted, never in git)
│   ├── BOT_TOKEN       — Telegram bot token
│   ├── CHAT_ID         — Telegram chat ID
│   ├── APP_TRV         — "35015,TP,2025" (application 1)
│   └── APP_WRK         — "18953,ZM,2026" (application 2)
│
└── GitHub Actions Cache
    └── status_cache.json  (restored before run, saved after)
```

**Runner:** GitHub-hosted Ubuntu (Python pre-installed, Playwright + Chromium installed each run)
**Cost:** $0.00 — public repo minutes are unlimited

---

## Application Aliases

| Alias | Number | Type | Year |
|-------|--------|------|------|
| TRV   | 35015  | TP   | 2025 |
| WRK   | 18953  | ZM   | 2026 |

Aliases appear in Telegram notification messages instead of raw number/type/year.

---

## Files Changed

### `config.py`
Read all values from environment variables instead of hardcoded. Parse `APP_TRV` and `APP_WRK` env vars (format: `"number,type,year"`) into the `APPLICATIONS` list. Add `alias` field to each application dict.

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

### `notifier.py`
`build_message()` uses `app["alias"]` for display instead of `{number}/{type}-{year}`.

```python
def build_message(app, status, phrase=None):
    label = app["alias"]          # "TRV" or "WRK"
    ...
    return f"🔴 Заявка {label}\n{text}"
```

### `monitor.py`
Remove the `FileHandler` from logging setup — Cloud/CI environments log to stdout only. Keep `StreamHandler`.

### `cache.py`
No changes. Reads/writes local `status_cache.json`. GitHub Actions Cache handles persistence between runs.

### `scraper.py`
No changes.

---

## New File: `.github/workflows/monitor.yml`

```yaml
name: IPC Monitor

on:
  schedule:
    - cron: "0 7,10,13,16 * * *"
  workflow_dispatch:  # allow manual trigger

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/cache@v4
        with:
          path: status_cache.json
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

`workflow_dispatch` is included so the monitor can be triggered manually from the GitHub UI at any time.

---

## Secrets to Configure in GitHub

After repo creation, set these four secrets in repo Settings → Secrets → Actions:

| Secret name | Value |
|-------------|-------|
| `BOT_TOKEN` | *(retrieve from local secure storage — not stored in this file)* |
| `CHAT_ID`   | *(retrieve from local secure storage — not stored in this file)* |
| `APP_TRV`   | `35015,TP,2025` |
| `APP_WRK`   | `18953,ZM,2026` |

---

## Cache Behaviour

`actions/cache@v4` with a static key `status-cache`:
- **Before run:** restores `status_cache.json` from cache (or starts empty on first run)
- **After run:** saves updated `status_cache.json` back to cache
- Cache expires after 7 days without access — impossible here (runs 4×/day)
- Cache storage limit: 10GB per repo — our file is ~1KB

---

## Logging

Stdout only. All output is visible in the GitHub Actions run log (Actions tab → workflow run → job). Logs are retained for 90 days.

---

## Local Development

The script still runs locally unchanged:

```bash
export BOT_TOKEN=... CHAT_ID=... APP_TRV=35015,TP,2025 APP_WRK=18953,ZM,2026
python monitor.py
```

The launchd setup on macOS can be retired once GitHub Actions is confirmed working.

---

## Out of Scope

- Telegram bot polling (ad-hoc checks via Telegram message) — currently runs locally, not migrated in this phase
- launchd removal — manual step after validation
