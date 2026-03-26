# IPC Monitor — Progress

_Last updated: 2026-03-26_

## Поточний статус заявок

| Заявка | Статус | Остання перевірка | Повідомлення надіслано |
|--------|--------|-------------------|------------------------|
| 35015/TP-2025 | 🔴 zpracovává se | 2026-03-26 | 2026-03-26 |
| 18953/ZM-2026 | 🔴 zpracovává se | 2026-03-26 | 2026-03-26 |

## Статус проекту

**Встановлено і працює.**

- ✅ Scraper підключився до ipc.gov.cz і зчитав статус обох заявок
- ✅ Telegram повідомлення надіслані (перевірка 2026-03-26 21:37)
- ✅ launchd зареєстровано: автоматичні перевірки 08:00 / 11:00 / 14:00 / 17:00
- ✅ 19/19 unit tests проходять

## Файли проекту

| Файл | Призначення | Стан |
|------|------------|------|
| `monitor.py` | Головний скрипт | ✅ |
| `scraper.py` | Playwright → ipc.gov.cz | ✅ виправлено (React Select, cookie consent) |
| `cache.py` | Кеш статусів | ✅ виправлено (approved variants) |
| `notifier.py` | Telegram повідомлення | ✅ |
| `config.py` | Токени і дані заявок | ✅ токени вставлені |
| `status_cache.json` | Останній відомий статус | ✅ актуальний |
| `install.sh` | Встановлення | ✅ |
| `com.ipc.monitor.plist` | launchd розклад | ✅ завантажено |
| `ipc_monitor.log` | Логи | ✅ пише |
| `tests/` | Unit tests | ✅ 19/19 pass |

## Відомі факти про сайт

- Дропдауни — **React Select** (не Vue-select як передбачалось)
- Cookie consent з'являється при кожному новому браузері — dismissed автоматично
- Кнопка підтвердження — `OVĚŘIT` (великі літери)
- Статус "в обробці": `"zpracovává se"`
- Статус "approved": `"předběžně vyhodnoceno kladně"` — ключове слово `kladně`

## Approved keywords (cache.py + notifier.py)

```python
["approved", "schváleno", "povolen", "kladně"]
```

## Що робити якщо scraper ламається

```bash
# Відкрити браузер видимо для debug
cd ~/ipc-monitor
venv/bin/python - <<'EOF'
import asyncio
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://ipc.gov.cz/informace-o-stavu-rizeni/")
        input("Inspect in DevTools, then Enter to close")
        await browser.close()

asyncio.run(debug())
EOF
```

## Git log

```
b3a21cb fix: add 'kladně' to approved keywords (IPC uses 'vyhodnoceno kladně')
efa3c33 fix: update scraper for React Select, cookie consent, correct button text; adapt to Python 3.9
5613cd8 feat: add launchd plist and install script
7a8a1ea feat: add main monitor orchestrator with retry and logging
fe964a5 feat: add Playwright scraper for ipc.gov.cz Vue form
0745b79 feat: add notifier module with Telegram message logic
9d91fe2 fix: treat all approved variants as equivalent in should_notify
404b2b8 feat: add cache module with status persistence logic
7846d48 feat: add project scaffold (config, requirements, CLAUDE.md)
```
