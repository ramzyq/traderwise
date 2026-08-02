from models.webhook import WebhookPayload


def test_payload_audio_message():
    payload = WebhookPayload.model_validate({
        "object": "whatsapp_business_account",
        "entry": [
            {"changes": [
                {"value": {"messages": [{"from": "233556000000", "type": "audio", "audio": {"id": "MEDIA1"}}]}}
            ]}
        ],
    })
    msg = payload.entry[0].changes[0].value.messages[0]
    assert msg.from_ == "233556000000"
    assert msg.type == "audio"
    assert msg.audio.id == "MEDIA1"
    assert msg.text is None


def test_payload_text_message():
    payload = WebhookPayload.model_validate({
        "object": "whatsapp_business_account",
        "entry": [
            {"changes": [
                {"value": {"messages": [{"from": "233556000000", "type": "text", "text": {"body": "hello"}}]}}
            ]}
        ],
    })
    msg = payload.entry[0].changes[0].value.messages[0]
    assert msg.text.body == "hello"
    assert msg.audio is None


def test_payload_no_messages():
    payload = WebhookPayload.model_validate({
        "object": "whatsapp_business_account",
        "entry": [{"changes": [{"value": {"messages": []}}]}],
    })
    msgs = payload.entry[0].changes[0].value.messages
    assert isinstance(msgs, list)
    assert len(msgs) == 0