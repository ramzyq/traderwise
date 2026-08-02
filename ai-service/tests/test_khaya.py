from unittest.mock import MagicMock

from services import khaya


def test_translate_returns_empty_without_key(monkeypatch):
    monkeypatch.setenv("KHAYA_API_KEY", "")
    assert khaya.khaya_translate("hello", "tw") == ""


def test_asr_returns_empty_without_key(monkeypatch):
    monkeypatch.setenv("KHAYA_API_KEY", "")
    assert khaya.khaya_asr(b"audio", "tw") == ""


def _fake_resp(text):
    resp = MagicMock()
    resp.json.return_value = text
    resp.text = text
    resp.raise_for_status.return_value = None
    return resp


def test_translate_hits_endpoint(monkeypatch):
    monkeypatch.setenv("KHAYA_API_KEY", "secret")
    calls = {}
    fake = _fake_resp("ekome")

    def fake_post(url, headers, json, timeout):
        calls["url"] = url
        calls["body"] = json
        calls["header"] = headers
        return fake

    monkeypatch.setattr(khaya.requests, "post", fake_post)
    result = khaya.khaya_translate("one", "en-gaa")
    assert result == "ekome"
    assert calls["url"] == khaya.TRANSLATE_URL
    assert calls["body"] == {"in": "one", "lang": "en-gaa"}
    assert calls["header"]["Ocp-Apim-Subscription-Key"] == "secret"


def test_asr_hits_endpoint(monkeypatch):
    monkeypatch.setenv("KHAYA_API_KEY", "secret")
    calls = {}
    fake = _fake_resp("transcribed text")

    def fake_post(url, headers, params, data, timeout):
        calls["url"] = url
        calls["params"] = params
        calls["data"] = data
        calls["headers"] = headers
        return fake

    monkeypatch.setattr(khaya.requests, "post", fake_post)
    result = khaya.khaya_asr(b"audiodata", "gaa")
    assert result == "transcribed text"
    assert calls["url"] == khaya.ASR_URL
    assert calls["params"] == {"language": "gaa"}
    assert calls["data"] == b"audiodata"