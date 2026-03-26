# IPC Monitor — Progress

_Last updated: 2026-03-27_

## Поточний статус заявок

| Аліас | Заявка | Статус | Остання перевірка |
|-------|--------|--------|-------------------|
| TRV | 35015/TP-2025 | 🔴 zpracovává se | 2026-03-27 |
| WRK | 18953/ZM-2026 | 🔴 zpracovává se | 2026-03-27 |

## Статус проекту

**Працює в хмарі 24/7 (GitHub Actions).**

- ✅ Scraper підключується до ipc.gov.cz і читає статус обох заявок
- ✅ Telegram повідомлення надіслані (перевірено 2026-03-27, аліаси TRV/WRK)
- ✅ GitHub Actions: автоматичні перевірки 08:00 / 11:00 / 14:00 / 17:00 Prague (зима)
- ✅ GitHub Actions Cache: status_cache.json зберігається між запусками
- ✅ Дублікати подавлені: другий запуск не надіслав повідомлення (кеш працює)
- ✅ Секрети в GitHub Actions Secrets — не в коді
- ✅ Shuffle-bag фрази: 41 фраза, не повторюється поки всі не використані
- ✅ 25/25 unit tests проходять
- ⚠️ Telegram bot polling (ad hoc перевірки) — працював локально, не мігрований в хмару

## Файли проекту

| Файл | Призначення | Стан |
|------|------------|------|
| `monitor.py` | Планові перевірки (single-shot, 4×/день) | ✅ stdout logging |
| `scraper.py` | Playwright → ipc.gov.cz | ✅ React Select, cookie consent |
| `cache.py` | Кеш статусів + shuffle-bag фраз | ✅ |
| `notifier.py` | Telegram повідомлення (аліаси TRV/WRK) | ✅ |
| `phrases.py` | Парсер phrases.md | ✅ |
| `phrases.md` | 41 фраза для статусу "в обробці" | ✅ |
| `config.py` | Читає з os.environ (без hardcode) | ✅ |
| `status_cache.json` | Останній статус + phrases_pool | ✅ GitHub Actions Cache |
| `.github/workflows/monitor.yml` | GitHub Actions workflow | ✅ ubuntu-22.04 |
| `tests/conftest.py` | Env vars для тестів | ✅ |
| `tests/test_cache.py` | Тести кешу | ✅ |
| `tests/test_config.py` | Тести config env vars | ✅ |
| `tests/test_notifier.py` | Тести повідомлень | ✅ |

## GitHub Actions

| Параметр | Значення |
|----------|---------|
| Репозиторій | https://github.com/EduardIng/ipc-monitor |
| Runner | ubuntu-22.04 |
| Cron | `0 7,10,13,16 * * *` UTC |
| Секрети | BOT_TOKEN, CHAT_ID, APP_TRV, APP_WRK |
| Cache key | `status-cache` (статичний, не інвалідується) |

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

## Наступні кроки

- [ ] **Рандомізація часу перевірок** — запуски в межах ±3 хвилин від 08/11/14/17 Prague
  Spec: `docs/superpowers/plans/2026-03-27-random-timing.md`

## Git log (останні)

```
98a1dd9 fix: remove unused pytest import from conftest
f20b707 fix: pin runner to ubuntu-22.04 (libasound2 missing on 24.04)
182cf6c feat: add GitHub Actions workflow for scheduled monitoring
17cfb17 feat: log to stdout only (removes local file handler)
68a74cc feat: use application alias (TRV/WRK) in Telegram messages
080c792 feat: read config from environment variables
30d47ed test: add conftest to set env vars before config import
38b1519 docs: fix plan per reviewer — clarify CHECK_HOURS drop, test edit scope, LOG_FILE safety
d640087 docs: add migration plan; scrub credentials from spec and plan docs
09f12a8 docs: add GitHub Actions migration design spec
```
