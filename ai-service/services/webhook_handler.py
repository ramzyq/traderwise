from models.webhook import WebhookPayload
from services.memory import Message, memory


class WebhookHandler:
    def __init__(self, processor, sender) -> None:
        self.processor = processor
        self.sender = sender

    def process(self, payload: WebhookPayload) -> None:
        if payload.object != "whatsapp_business_account":
            return
        if not payload.entry:
            return
        for entry in payload.entry:
            for change in entry.changes:
                for msg in change.value.messages:
                    self._handle_message(msg)

    def _save(self, user_id, user_text, reply):
        history = memory.get(user_id)
        history.append(Message(role="user", content=user_text))
        history.append(Message(role="assistant", content=reply))
        memory.save(user_id, history)

    def _handle_message(self, msg):
        user_id = msg.from_
        if msg.type == "text" and msg.text:
            text = msg.text.body.strip()
            if text == "":
                self.sender(user_id, "I could not understand that. Please try again.")
                return
            command_reply = self._command_reply(text, user_id)
            if command_reply is not None:
                self._save(user_id, text, command_reply)
                self.sender(user_id, command_reply)
                return
            reply = self.processor.handle_text(text, user_id, message_id=msg.id)
            self._save(user_id, text, reply)
            self.sender(user_id, reply)
        elif msg.type == "audio" and msg.audio:
            reply = self.processor.handle_audio(msg.audio.id, user_id, message_id=msg.id)
            self.sender(user_id, reply)

    def _command_reply(self, text: str, user_id: str) -> str | None:
        lowered = text.lower()
        if lowered == "start":
            self.memory_clear(user_id)
            return "Hello! I'm Ama... (greeting)"
        if lowered in ("reset", "start over"):
            self.memory_clear(user_id)
            return "Chat cleared. What's on your mind with the business?"
        if lowered == "help":
            return "TraderWise commands: start, reset, help, delete. Or just tell me about your business."
        if lowered == "delete":
            self.memory_clear(user_id)
            return "Your data has been cleared. You can reach us anytime."
        return None

    def memory_clear(self, user_id):
        memory.clear(user_id)