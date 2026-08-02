import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_get_webhook_verify_bad_token(client, monkeypatch):
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "sekrit")
    resp = client.get("/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "123"})
    assert resp.status_code == 403
    assert resp.text != "123"


def test_get_webhook_verify_good_token(client, monkeypatch):
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "sekrit")
    resp = client.get("/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "sekrit", "hub.challenge": "42"})
    assert resp.status_code == 200
    assert resp.text == "42"


def test_post_webhook_enqueues_task(client, monkeypatch):
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "sekrit")
    body = {
        "object": "whatsapp_business_account",
        "entry": [
            {"changes": [{"value": {"messages": [
                {"from": "233556000000", "type": "text", "text": {"body": "restock"}}
            ]}}]}
        ],
    }
    with patch("main.process_webhook.delay") as mock_delay:
        resp = client.post("/webhook", json=body)
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
        assert mock_delay.called


def test_post_webhook_non_whatsapp_not_enqueued(client):
    body = {"object": "not_whatsapp", "entry": []}
    with patch("main.process_webhook.delay") as mock_delay:
        resp = client.post("/webhook", json=body)
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
        assert not mock_delay.called


def test_post_webhook_broker_down_still_returns_ok(client):
    body = {
        "object": "whatsapp_business_account",
        "entry": [
            {"changes": [{"value": {"messages": [
                {"from": "233556000000", "type": "text", "text": {"body": "restock"}}
            ]}}]}
        ],
    }
    with patch("main.process_webhook.delay", side_effect=RuntimeError("broker down")):
        resp = client.post("/webhook", json=body)
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


def test_post_webhook_bad_signature_rejected(client, monkeypatch):
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "secret123")
    body = {"object": "whatsapp_business_account"}
    resp = client.post("/webhook", json=body, headers={"X-Hub-Signature-256": "sha256=deadbeef"})
    assert resp.status_code == 401


def test_post_webhook_valid_signature_accepted(client, monkeypatch):
    import hmac
    import hashlib
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "secret123")
    body_bytes = b'{"object": "ignore"}'
    sig = "sha256=" + hmac.new(b"secret123", body_bytes, hashlib.sha256).hexdigest()
    resp = client.post(
        "/webhook",
        content=body_bytes,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig},
    )
    assert resp.status_code == 200