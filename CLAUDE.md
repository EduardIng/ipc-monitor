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
- Секрети (BOT_TOKEN, CHAT_ID, APP_TRV, APP_WRK, APP_OLD) зберігаються в GitHub Actions Secrets — не в коді
- config.py читає всі значення з os.environ — hardcode відсутній
- GitHub Actions runner: ubuntu-22.04 (не ubuntu-latest — libasound2 відсутній в Ubuntu 24.04)
- Логування тільки в stdout (GitHub Actions захоплює автоматично)

## Структура файлів
~/ipc-monitor/
├── CLAUDE.md                        ← цей файл
├── monitor.py                       ← основний скрипт (single-shot)
├── config.py                        ← читає з os.environ (без hardcode)
├── cache.py                         ← логіка кешу + shuffle-bag фраз
├── notifier.py                      ← Telegram повідомлення (використовує alias)
├── scraper.py                       ← Playwright scraping
├── phrases.py                       ← парсер phrases.md
├── phrases.md                       ← 41 фраза для статусу "в обробці"
├── status_cache.json                ← кеш статусів (локально; в CI — GitHub Actions Cache)
├── requirements.txt                 ← залежності
├── .github/workflows/monitor.yml   ← GitHub Actions workflow
├── tests/                           ← unit tests (25 pass)
│   ├── conftest.py                  ← env vars для тестів
│   ├── test_cache.py
│   ├── test_config.py
│   └── test_notifier.py
└── docs/superpowers/
    ├── specs/                       ← design docs
    └── plans/                       ← implementation plans
