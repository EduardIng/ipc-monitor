# IPC Visa Monitor — Design Spec
**Date:** 2026-03-26

## Goal
Monitor two Czech residence permit applications on ipc.gov.cz and send Telegram notifications when status changes.

## Applications
- 35015 / TP / 2025
- 18953 / ZM / 2026

## Architecture
Standalone Python script triggered by macOS launchd 4×/day (08:00, 11:00, 14:00, 17:00 Europe/Prague). No server, no queue.

## Components

| File | Purpose |
|------|---------|
| `monitor.py` | Playwright scraper + notification logic |
| `config.py` | Tokens, applications, schedule |
| `status_cache.json` | Persists previous status + last-notified date between runs |
| `com.ipc.monitor.plist` | launchd schedule config |
| `install.sh` | One-command setup |
| `requirements.txt` | Python dependencies |
| `ipc_monitor.log` | Timestamped log file |

## Scraping Approach
- **Playwright async API** with headless Chromium — required because ipc.gov.cz is a Vue.js SPA
- Form fields: `input[name="proceedings.referenceNumber"]` for number
- Dropdowns are custom Vue components — interact via `page.click()` on option text, not `<select>` value
- Use `page.wait_for_selector()` throughout, never `time.sleep()`
- Retry: 3 attempts with 30s pause on failure

## Notification Logic

| Status | Action |
|--------|--------|
| "zpracovává se" | Send once per day (first check of the day only) |
| approved / schváleno / povolen | Send once, never repeat |
| Any other status | Send immediately with exact page text |
| Site unreachable after 3 retries | Send error message |

## Message Templates
See CLAUDE.md for exact Ukrainian message text.

## State Management
`status_cache.json` stores per-application:
- `last_status`: previous status string
- `last_notified_date`: ISO date of last "zpracovává se" notification

## Install Flow
`bash install.sh` → creates venv → installs deps → installs Playwright Chromium → registers launchd → prints instructions to add tokens then run manual test.

Manual test after tokens: `python ~/ipc-monitor/monitor.py`
