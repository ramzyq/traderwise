import pytest
from fastapi.testclient import TestClient

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