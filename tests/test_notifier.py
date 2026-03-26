import pytest
from unittest.mock import patch, MagicMock
import notifier

APP_TP = {"number": "35015", "type": "TP", "year": "2025"}
APP_ZM = {"number": "18953", "type": "ZM", "year": "2026"}


def test_build_message_processing():
    msg = notifier.build_message(APP_TP, "Vaše žádost se zpracovává se.")
    assert "🔴 Заявка 35015/TP-2025" in msg
    assert "покидьки" in msg


def test_build_message_approved_schvaleno():
    msg = notifier.build_message(APP_TP, "Žádost byla schváleno.")
    assert "🟢 Заявка 35015/TP-2025" in msg
    assert "Уроди" in msg


def test_build_message_approved_povolen():
    msg = notifier.build_message(APP_ZM, "Pobyt povolen.")
    assert "🟢 Заявка 18953/ZM-2026" in msg
    assert "Уроди" in msg


def test_build_message_approved_english():
    msg = notifier.build_message(APP_TP, "Application approved.")
    assert "🟢 Заявка 35015/TP-2025" in msg


def test_build_message_other_status():
    msg = notifier.build_message(APP_TP, "Žádost zamítnuta.")
    assert "⚠️ Заявка 35015/TP-2025" in msg
    assert "Žádost zamítnuta." in msg
    assert "Перевір сайт вручну!" in msg


def test_send_telegram_calls_api(monkeypatch):
    mock_post = MagicMock()
    mock_post.return_value.raise_for_status = MagicMock()
    monkeypatch.setattr("notifier.requests.post", mock_post)
    monkeypatch.setattr("notifier.config.BOT_TOKEN", "test_token")
    monkeypatch.setattr("notifier.config.CHAT_ID", "12345")

    notifier.send_telegram("hello")

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert "test_token" in call_kwargs[0][0]
    assert call_kwargs[1]["json"]["text"] == "hello"
    assert call_kwargs[1]["json"]["chat_id"] == "12345"


def test_send_error_sends_correct_message(monkeypatch):
    sent = []
    monkeypatch.setattr("notifier.send_telegram", lambda msg: sent.append(msg))
    notifier.send_error()
    assert len(sent) == 1
    assert "❌ IPC Monitor" in sent[0]
    assert "недоступний" in sent[0]
