from services.webhook_handler import WebhookHandler
from models.webhook import WebhookPayload


class FakeProcessor:
    def handle_text(self, message, phone):
        return f"REPLY to {message}"

    def handle_audio(self, audio_url, phone, access_token):
        return f"AUDIO REPLY {audio_url}"


class FakeSender:
    def __init__(self):
        self.sent = []

    def send(self, to, text):
        self.sent.append((to, text))


def test_non_whatsapp_object_is_ignored():
    sender = FakeSender()
    handler = WebhookHandler(processor=FakeProcessor(), sender=sender.send)
    payload = WebhookPayload(object="not_whatsapp", entry=[])
    handler.process(payload)
    assert sender.sent == []


def test_start_command():
    sender = FakeSender()
    handler = WebhookHandler(processor=FakeProcessor(), sender=sender.send)
    payload = WebhookPayload.model_validate({
        "object": "whatsapp_business_account",
        "entry": [{"changes": [{"value": {"messages": [
            {"from": "233556000000", "type": "text", "text": {"body": "start"}}
        ]}}]}],
    })
    handler.process(payload)
    assert len(sender.sent) == 1
    assert "I'm Ama" in sender.sent[0][1]


def test_text_routed_to_processor():
    sender = FakeSender()
    handler = WebhookHandler(processor=FakeProcessor(), sender=sender.send)
    payload = WebhookPayload.model_validate({
        "object": "whatsapp_business_account",
        "entry": [{"changes": [{"value": {"messages": [
            {"from": "233556000000", "type": "text", "text": {"body": "how to restock"}}
        ]}}]}],
    })
    handler.process(payload)
    assert sender.sent == [("233556000000", "REPLY to how to restock")]


def test_memory_saved():
    sender = FakeSender()
    handler = WebhookHandler(processor=FakeProcessor(), sender=sender.send)
    payload = WebhookPayload.model_validate({
        "object": "whatsapp_business_account",
        "entry": [{"changes": [{"value": {"messages": [
            {"from": "233556000000", "type": "text", "text": {"body": "hola"}}
        ]}}]}],
    })
    handler.process(payload)
    from services.memory import memory
    hist = memory.get("233556000000")
    assert hist[-2].role == "user"
    assert hist[-1].role == "assistant"
    memory.clear("233556000000")