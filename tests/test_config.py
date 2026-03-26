import os
import pytest


def test_parse_app_trv(monkeypatch):
    monkeypatch.setenv("APP_TRV", "35015,TP,2025")
    import importlib, config
    importlib.reload(config)
    app = config._parse_app("APP_TRV", "TRV")
    assert app == {"number": "35015", "type": "TP", "year": "2025", "alias": "TRV"}


def test_parse_app_wrk(monkeypatch):
    monkeypatch.setenv("APP_WRK", "18953,ZM,2026")
    import importlib, config
    importlib.reload(config)
    app = config._parse_app("APP_WRK", "WRK")
    assert app == {"number": "18953", "type": "ZM", "year": "2026", "alias": "WRK"}


def test_applications_list_has_two_entries():
    import importlib, config
    importlib.reload(config)
    assert len(config.APPLICATIONS) == 2
    aliases = [a["alias"] for a in config.APPLICATIONS]
    assert "TRV" in aliases
    assert "WRK" in aliases


def test_bot_token_from_env(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "my_secret_token")
    import importlib, config
    importlib.reload(config)
    assert config.BOT_TOKEN == "my_secret_token"


def test_chat_id_from_env(monkeypatch):
    monkeypatch.setenv("CHAT_ID", "999")
    import importlib, config
    importlib.reload(config)
    assert config.CHAT_ID == "999"


def test_missing_bot_token_raises(monkeypatch):
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    import importlib, config
    with pytest.raises(KeyError):
        importlib.reload(config)
