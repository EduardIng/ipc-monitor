import os
import pytest

# Set env vars before any test module imports config
os.environ.setdefault("BOT_TOKEN", "test_token")
os.environ.setdefault("CHAT_ID", "123456")
os.environ.setdefault("APP_TRV", "35015,TP,2025")
os.environ.setdefault("APP_WRK", "18953,ZM,2026")
