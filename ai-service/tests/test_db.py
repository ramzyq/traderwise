import services.db as db


def _monkey(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.db"))
    monkeypatch.delenv("DATABASE_URL", raising=False)


def test_save_interaction_with_meta_message_id(monkeypatch, tmp_path):
    _monkey(monkeypatch, tmp_path)
    db.save_interaction(
        phone="233550000001",
        transcription=None,
        claude_input="hello",
        claude_output="hi there",
        final_reply="hi there",
        meta_message_id="wamid.abc123",
        status="pending",
    )
    assert db.message_exists("wamid.abc123") is True
    assert db.message_exists(None) is False
    assert db.message_exists("nope") is False


def test_save_interaction_updates_existing_row(monkeypatch, tmp_path):
    _monkey(monkeypatch, tmp_path)
    db.save_interaction("234", None, "in", "out", "reply", meta_message_id="mid1", status="pending")
    db.message_exists("mid1")
    db.update_interaction_status("mid1", "completed")
    assert db.message_exists("mid1") is True


def test_update_interaction_status_no_crash_when_missing(monkeypatch, tmp_path):
    _monkey(monkeypatch, tmp_path)
    db.update_interaction_status("ghost", "failed")


def test_save_without_meta_message_id_still_works(monkeypatch, tmp_path):
    _monkey(monkeypatch, tmp_path)
    db.save_interaction("2345", None, "in", "out", "reply", status="completed")
    assert db.message_exists("x") is False


def test_webhook_handler_skips_duplicate(monkeypatch, tmp_path):
    _monkey(monkeypatch, tmp_path)
    db.save_interaction("555", None, "same", "o", "r", meta_message_id="dup.id", status="completed")
    from models.webhook import WebhookPayload
    from services.webhook_handler import WebhookHandler

    sent = []
    payload = WebhookPayload.model_validate({
        "object": "whatsapp_business_account",
        "entry": [{"changes": [{"value": {"messages": [
            {"id": "dup.id", "from": "233550000001", "type": "text", "text": {"body": "hey"}}
        ]}}]}],
    })
    handler = WebhookHandler(processor=object(), sender=lambda to, text: sent.append(text))
    handler.process(payload)
    assert sent == []