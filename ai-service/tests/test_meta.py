import requests

from services import meta


def test_send_message_success(monkeypatch):
    calls = {}

    class FakeResp:
        status_code = 200

        def raise_for_status(self):
            pass

    def fake_post(url, json=None, headers=None, timeout=None):
        calls["url"] = url
        calls["json"] = json
        return FakeResp()

    monkeypatch.setattr(meta.requests, "post", fake_post)
    meta.send_message("12345", "tok", "2335566778", "hello")

    assert calls["url"] == "https://graph.facebook.com/v19.0/12345/messages"
    assert calls["json"] == {
        "messaging_product": "whatsapp",
        "to": "2335566778",
        "type": "text",
        "text": {"body": "hello"},
    }


def test_send_message_error(monkeypatch):
    class FakeResp:
        status_code = 500

        def raise_for_status(self):
            raise Exception("boom")

    def fake_post(url, json=None, headers=None, timeout=None):
        return FakeResp()

    monkeypatch.setattr(meta.requests, "post", fake_post)
    try:
        meta.send_message("12345", "tok", "233556600000", "hi")
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass


def test_resolve_media_url(monkeypatch):
    class FakeResp:
        def json(self):
            return {"url": "https://cdn.example/audio.ogg"}

        def raise_for_status(self):
            pass

    def fake_get(url, headers=None, timeout=None):
        return FakeResp()

    monkeypatch.setattr(meta.requests, "get", fake_get)
    url = meta.resolve_media_url("tok", "MEDIA1")
    assert url == "https://cdn.example/audio.ogg"