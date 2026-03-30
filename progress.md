# IPC Monitor — Progress

_Last updated: 2026-03-30_

## Поточний статус заявок

| Аліас | Заявка | Статус | Остання перевірка |
|-------|--------|--------|-------------------|
| TRV | 35015/TP-2025 | 🔴 zpracovává se | 2026-03-30 |
| WRK | 18953/ZM-2026 | 🔴 zpracovává se | 2026-03-30 |
| OLD | 30916/TP-2025 | 🔴 zpracovává se | 2026-03-30 |

## Статус проекту

**Працює в хмарі 24/7 (GitHub Actions).**

- ✅ Scraper підключується до ipc.gov.cz і читає статус всіх 3 заявок (TRV/WRK/OLD)
- ✅ Telegram повідомлення надіслані (аліаси TRV/WRK/OLD)
- ✅ GitHub Actions: автоматичні перевірки 09:00 / 12:00 / 15:00 / 18:00 Prague (літо, UTC+2)
- ✅ GitHub Actions Cache: status_cache.json зберігається між запусками
- ✅ Дублікати подавлені: кеш працює
- ✅ Секрети в GitHub Actions Secrets — не в коді
- ✅ Shuffle-bag фрази: 41 фраза, не повторюється поки всі не використані
- ✅ 25/25 unit tests проходять
- ✅ bot.yml: GHA polling Telegram кожні 5 хв (Mon-Fri) → запускає adhoc.py при повідомленні
- ✅ bot.py: локальний long-polling (launchd) для миттєвих ad hoc перевірок коли ноутбук увімкнений
- ✅ ad hoc check в bot.py виконується в background thread (не блокує poll loop при сні ноутбука)

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
| `bot.py` | Локальний Telegram long-polling (launchd) | ✅ background thread |
| `adhoc.py` | Ad hoc перевірка для GHA (завжди надсилає) | ✅ |
| `poll.py` | Lightweight Telegram poller для bot.yml | ✅ |
| `.github/workflows/monitor.yml` | GitHub Actions scheduled workflow | ✅ ubuntu-22.04 |
| `.github/workflows/bot.yml` | GHA bot: poll */5min → adhoc якщо є повідомлення | ✅ + workflow_dispatch |
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
| Секрети | BOT_TOKEN, CHAT_ID, APP_TRV, APP_WRK, APP_OLD |
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
5319957 fix: restore bot.yml schedule, add workflow_dispatch, thread ad hoc check
586aeb3 fix: restrict bot.yml poll to weekdays only (Mon-Fri)
dd0bf58 fix: switch poll.py from urllib to requests + strip token whitespace
678a19b debug: log BOT_TOKEN presence and length in poll.py
dc479c9 fix: replace inline heredoc with poll.py to fix 401 on Telegram poll
780e722 feat: skip weekends for scheduled checks (Mon-Fri only)
```
