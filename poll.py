# ~/ipc-monitor/poll.py
"""
Lightweight Telegram poller for GitHub Actions bot.yml.
Reads BOT_TOKEN and CHAT_ID from env, checks for new messages,
writes triggered=true/false to GITHUB_OUTPUT.
Persists last update_id via telegram_offset.txt (cached by GHA).
"""
import os

import requests

bot_token = os.environ.get("BOT_TOKEN", "").strip()
chat_id = os.environ.get("CHAT_ID", "").strip()

print(f"BOT_TOKEN: {'SET len=' + str(len(bot_token)) if bot_token else 'EMPTY'}")
print(f"CHAT_ID: {'SET len=' + str(len(chat_id)) if chat_id else 'EMPTY'}")

if not bot_token:
    print("ERROR: BOT_TOKEN is empty — check GitHub Actions secret name")
    raise SystemExit(1)

offset = None
if os.path.exists("telegram_offset.txt"):
    try:
        offset = int(open("telegram_offset.txt").read().strip())
    except Exception:
        pass

params: dict = {"timeout": 0, "allowed_updates": ["message"]}
if offset is not None:
    params["offset"] = offset

resp = requests.get(
    f"https://api.telegram.org/bot{bot_token}/getUpdates",
    params=params,
    timeout=10,
)
resp.raise_for_status()
updates = resp.json().get("result", [])

triggered = False
new_offset = offset
for update in updates:
    new_offset = update["update_id"] + 1
    msg = update.get("message", {})
    if str(msg.get("chat", {}).get("id", "")) == str(chat_id):
        triggered = True

if new_offset is not None:
    open("telegram_offset.txt", "w").write(str(new_offset))

flag = "true" if triggered else "false"
print(f"triggered={flag}")
with open(os.environ["GITHUB_OUTPUT"], "a") as f:
    f.write(f"triggered={flag}\n")
