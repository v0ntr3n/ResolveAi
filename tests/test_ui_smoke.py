import os

from ui.app import backend_url, detect_local_language


def test_ui_helpers():
    assert backend_url().startswith("http")
    assert detect_local_language("Chính sách hoàn tiền") == "vi"
    assert detect_local_language("Where is my order?") == "en"


def test_backend_url_uses_hostport_when_present(monkeypatch):
    monkeypatch.delenv("RESOLVEAI_BACKEND_URL", raising=False)
    monkeypatch.setenv("RESOLVEAI_BACKEND_HOSTPORT", "resolveai-api:10000")

    assert backend_url() == "http://resolveai-api:10000"
