# IPC Visa Monitor — Project Reference

Цей файл є головним референсом для всіх неоднозначних ситуацій в проекті.
При будь-яких сумнівах — читай цей файл першим.

## Мета проекту
Автоматичний моніторинг трьох заявок на дозвіл проживання в Чехії на сайті ipc.gov.cz.
Сповіщення через Telegram бота.

## Заявки
- Заявка 1: номер 35015, тип TP, рік 2025 — аліас **TRV**
- Заявка 2: номер 18953, тип ZM, рік 2026 — аліас **WRK**
- Заявка 3: номер 30916, тип TP, рік 2025 — аліас **OLD**

Аліаси відображаються в Telegram повідомленнях замість повного номера.

## Технічний стек
- Python 3.11+
- Playwright (headless Chromium) — НЕ requests/BeautifulSoup, сайт на Vue.js
- Telegram Bot API через requests
- **GitHub Actions** для розкладу (не launchd — ноутбук може бути вимкнений)
- **bot.py** — локальний long-polling listener (launchd, KeepAlive) для ручних перевірок
- GitHub Actions Cache для зберігання status_cache.json між запусками
- GitHub Actions Secrets для токенів і даних заявок
- Репозиторій: https://github.com/EduardIng/ipc-monitor (публічний)

## Розклад перевірок
08:00, 11:00, 14:00, 17:00 за Europe/Prague (зима)
09:00, 12:00, 15:00, 18:00 за Europe/Prague (літо, +1г зміна DST — прийнятно)
GitHub Actions cron: `0 7,10,13,16 * * *` UTC

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
- Дропдауни на сайті кастомні (React Select) — клікати по тексту опції, НЕ по value
- page.wait_for_selector() замість time.sleep()
- Retry: 3 спроби з паузою 30 секунд
- Попередній статус зберігається в status_cache.json (персистується через GitHub Actions Cache)
- GHA cache key: `status-cache-${{ github.run_id }}` з restore-keys `status-cache` — завжди зберігає після кожного запуску
- GHA кешує pip (~/.cache/pip) і Playwright (~/.cache/ms-playwright) для швидкого запуску
- Секрети (BOT_TOKEN, CHAT_ID, APP_TRV, APP_WRK, APP_OLD) зберігаються в GitHub Actions Secrets і в ~/Library/LaunchAgents/com.ipc.bot.plist (локально) — ніколи не в коді репозиторію
- config.py читає всі значення з os.environ — hardcode відсутній
- bot.py: stdout-only logging; env vars отримує через launchd plist (не через shell)
- GitHub Actions runner: ubuntu-22.04 (не ubuntu-latest — libasound2 відсутній в Ubuntu 24.04)
- Логування тільки в stdout (GitHub Actions захоплює автоматично; launchd → ipc_monitor.log)

## Структура файлів
~/ipc-monitor/
├── CLAUDE.md                        ← цей файл
├── monitor.py                       ← основний скрипт (single-shot, запускається GHA)
├── bot.py                           ← Telegram long-polling listener (launchd, ручні перевірки)
├── config.py                        ← читає з os.environ (без hardcode)
├── cache.py                         ← логіка кешу + shuffle-bag фраз
├── notifier.py                      ← Telegram повідомлення (використовує alias)
├── scraper.py                       ← Playwright scraping
├── phrases.py                       ← парсер phrases.md
├── phrases.md                       ← 41 фраза для статусу "в обробці"
├── status_cache.json                ← кеш статусів (локально; в CI — GitHub Actions Cache)
├── requirements.txt                 ← залежності
├── com.ipc.bot.plist                ← launchd template (плейсхолдери __BOT_TOKEN__ тощо)
├── com.ipc.monitor.plist            ← launchd template (не використовується в поточній версії)
├── install.sh                       ← встановлює venv, plist, Playwright
├── .github/workflows/monitor.yml   ← GitHub Actions workflow
├── tests/                           ← unit tests
│   ├── conftest.py                  ← env vars для тестів (APP_TRV, APP_WRK, APP_OLD)
│   ├── test_cache.py
│   ├── test_config.py
│   └── test_notifier.py
└── docs/superpowers/
    ├── specs/                       ← design docs
    └── plans/                       ← implementation plans

## Секрети — де зберігаються
⚠️ Ніколи не коміть реальні токени/ID в репозиторій!
- **GitHub Actions**: Settings → Secrets → Actions (BOT_TOKEN, CHAT_ID, APP_TRV, APP_WRK, APP_OLD)
- **Локально (bot.py)**: ~/Library/LaunchAgents/com.ipc.bot.plist — тільки на диску, не в репо
- **Шаблон plist** у репо містить лише плейсхолдери (__BOT_TOKEN__, __CHAT_ID__ тощо)
