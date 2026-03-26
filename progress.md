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
- ✅ Telegram бот слухає повідомлення — будь-яке повідомлення → миттєва перевірка
- ✅ Shuffle-bag фрази: 41 фраза, не повторюється поки всі не використані
- ✅ 19/19 unit tests проходять

## Файли проекту

| Файл | Призначення | Стан |
|------|------------|------|
| `monitor.py` | Планові перевірки (4×/день) | ✅ |
| `bot.py` | Telegram polling — ad hoc перевірки | ✅ |
| `scraper.py` | Playwright → ipc.gov.cz | ✅ виправлено (React Select, cookie consent) |
| `cache.py` | Кеш статусів + shuffle-bag фраз | ✅ |
| `notifier.py` | Telegram повідомлення | ✅ |
| `phrases.py` | Парсер phrases.md | ✅ |
| `phrases.md` | 41 фраза для статусу "в обробці" | ✅ |
| `config.py` | Токени і дані заявок | ✅ токени вставлені |
| `status_cache.json` | Останній статус + phrases_pool | ✅ актуальний |
| `install.sh` | Встановлення одною командою | ✅ реєструє обидва launchd jobs |
| `com.ipc.monitor.plist` | launchd: планові перевірки | ✅ завантажено |
| `com.ipc.bot.plist` | launchd: bot polling (KeepAlive) | ✅ завантажено |
| `ipc_monitor.log` | Логи | ✅ пише |
| `tests/` | Unit tests | ✅ 19/19 pass |

## Launchd jobs

| Job | Тип | Розклад |
|-----|-----|---------|
| `com.ipc.monitor` | StartCalendarInterval | 08:00, 11:00, 14:00, 17:00 |
| `com.ipc.bot` | KeepAlive (постійно) | завжди активний |

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

## Фрази

41 фраза в `phrases.md` — списки A (30, іронічні), Б (10, з лайкою), В (1, фольклорна).
Shuffle-bag стан зберігається в `status_cache.json` → `phrases_pool`.

## Що робити якщо scraper ламається

```bash
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
ee7d922 feat: add Telegram bot polling — any message triggers ad hoc check
0ce474e feat: shuffle-bag phrase rotation — 41 phrases, no repeats until all used
bb71a9d docs: add list C with one folkloric phrase
5c06b51 docs: add phrase lists A and B for processing status messages
40a148d docs: add progress.md with current project status
b3a21cb fix: add 'kladně' to approved keywords (IPC uses 'vyhodnoceno kladně')
efa3c33 fix: update scraper for React Select, cookie consent, correct button text; adapt to Python 3.9
5613cd8 feat: add launchd plist and install script
7a8a1ea feat: add main monitor orchestrator with retry and logging
fe964a5 feat: add Playwright scraper for ipc.gov.cz Vue form
0745b79 feat: add notifier module with Telegram message logic
9d91fe2 fix: treat all approved variants as equivalent in should_notify
404b2b8 feat: add cache module with status persistence logic
7846d48 feat: add project scaffold (config, requirements, CLAUDE.md)
928e817 chore: add design spec and implementation plan
```
