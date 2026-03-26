import json
import os
import tempfile
from datetime import date, timedelta
import pytest

import cache


@pytest.fixture
def tmp_cache_file(tmp_path, monkeypatch):
    cache_file = tmp_path / "status_cache.json"
    monkeypatch.setattr(cache, "CACHE_FILE", str(cache_file))
    return cache_file


def test_load_cache_returns_empty_dict_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_FILE", str(tmp_path / "nonexistent.json"))
    result = cache.load_cache()
    assert result == {}


def test_save_and_load_roundtrip(tmp_cache_file):
    data = {"key": {"last_status": "processing", "last_notified_date": "2026-01-01"}}
    cache.save_cache(data)
    loaded = cache.load_cache()
    assert loaded == data


def test_get_app_key():
    app = {"number": "35015", "type": "TP", "year": "2025"}
    assert cache.get_app_key(app) == "35015/TP-2025"


def test_should_notify_processing_first_time():
    c = {}
    assert cache.should_notify(c, "35015/TP-2025", "zpracovává se") is True


def test_should_notify_processing_same_day_returns_false():
    today = date.today().isoformat()
    c = {"35015/TP-2025": {"last_status": "zpracovává se", "last_notified_date": today}}
    assert cache.should_notify(c, "35015/TP-2025", "zpracovává se") is False


def test_should_notify_processing_new_day_returns_true():
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    c = {"35015/TP-2025": {"last_status": "zpracovává se", "last_notified_date": yesterday}}
    assert cache.should_notify(c, "35015/TP-2025", "zpracovává se") is True


def test_should_notify_approved_first_time():
    c = {}
    assert cache.should_notify(c, "35015/TP-2025", "schváleno") is True


def test_should_notify_approved_already_notified():
    c = {"35015/TP-2025": {"last_status": "schváleno", "last_notified_date": "2026-01-01"}}
    assert cache.should_notify(c, "35015/TP-2025", "schváleno") is False


def test_should_notify_other_status_new():
    c = {}
    assert cache.should_notify(c, "35015/TP-2025", "nějaký jiný stav") is True


def test_should_notify_other_status_unchanged():
    c = {"35015/TP-2025": {"last_status": "nějaký jiný stav", "last_notified_date": "2026-01-01"}}
    assert cache.should_notify(c, "35015/TP-2025", "nějaký jiný stav") is False


def test_update_cache_sets_today():
    c = {}
    cache.update_cache(c, "35015/TP-2025", "zpracovává se")
    assert c["35015/TP-2025"]["last_status"] == "zpracovává se"
    assert c["35015/TP-2025"]["last_notified_date"] == date.today().isoformat()
