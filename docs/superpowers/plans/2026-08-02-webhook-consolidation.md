# Webhook Consolidation into FastAPI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the Meta WhatsApp webhook (currently in deprecated `backend-go/`) into the Python FastAPI `ai-service`, so the whole system runs as one service that receives Meta webhooks, handles built-in commands, processes voice/text messages through the existing AI pipeline, and replies over the Meta Graph API.

**Architecture:** FastAPI gains `GET /webhook` (Meta SHA verification handshake) and `POST /webhook` (message handler). A new `services/whatsapp.py` wraps the Meta Graph API (send text, resolve audio media URL). A new `services/memory.py` is an in-process conversation history store. A new `services/webhook.py` parses the Meta payload (Pydantic request model) and orchestrates command handling + message routing to the existing `ChatPipeline` and `transcribe` service. Config values move into the service's `.env`. The deprecated Go and Node.js backends are removed at the end.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, `requests`, pytest.

## Global Constraints

- Meta webhook verify endpoint: `GET /webhook` reads query params `hub.mode`, `hub.verify_token`, `hub.challenge`. Valid when `hub.mode == "subscribe"` and `hub.verify_token` equals `WHATSAPP_VERIFY_TOKEN`; respond with plain-text `hub.challenge`, else 403.
- Meta message endpoint: `POST /webhook`. Must respond `200 OK` immediately. Only acts on `object == "whatsapp_business_account"` and the first entry/change/message.
- Meta Graph API base: `https://graph.facebook.com/v19.0/`. Send uses `/<PHONE_NUMBER_ID>/messages`; audio resolve uses `/<MEDIA_ID>` with `Authorization: Bearer <WHATSAPP_ACCESS_TOKEN>`.
- Built-in commands (case-insensitive, trimmed): `start`, `reset`/`start over`, `help`, `DELETE me`. Non-command text is routed to the AI pipeline.
- `What will remain`: messages over media (voice) are resolved via media ID → audio URL → `transcribe_from_audio_url`, then routed through the pipeline as text.
- Webhook must call the AI pipeline and Graph API **in-process** (no HTTP hop to self). No asynchronous queue in this increment — queue is a later issue.
- Network calls in tests are mocked; tests never hit the real Meta or Groq APIs.
- `services/claude_client.py` legacy module is untouched and remains uncommitted-but-present; it is not linked to the new pipeline.
- `httpx` must be available for `FastAPI.TestClient`; if `tests/test_webhook.py` fails to import it, install it: `python -m pip install "httpx"` in the venv. (httpx is a transitive dep of FastAPI's TestClient.)

---

### Task 1: Add settings module for WhatsApp env vars

**Files:**
- Create: `ai-service/settings.py`
- Test: `ai-service/tests/test_settings.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `from settings import settings` — a module-level instance with attributes `whatsapp_access_token: str`, `whatsapp_phone_number_id: str`, `whatsapp_verify_token: str`, default `.graph_base = "https://graph.facebook.com/v19.0/"`. Also `from settings import get_webhook_secret` not needed; tokens read via `settings`.

- [ ] **Step 1: Write the failing test**

Create `ai-service/tests/test_settings.py`:

```python
from settings import Settings


def test_settings_defaults(monkeypatch):
    monkeypatch.delenv("WHATSAPP_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("WHATSAPP_PHONE_NUMBER_ID", raising=False)
    monkeypatch.delenv("WHATSAPP_VERIFY_TOKEN", raising=False)
    s = Settings()
    assert s.whatsapp_access_token == ""
    assert s.whatsapp_phone_number_id == ""
    assert s.whatsapp_verify_token == ""
    assert s.graph_base == "https://graph.facebook.com/v19.0/"


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "tok_abc")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "12345")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "veriftok")
    s = Settings()
    assert s.whatsapp_access_token == "tok_abc"
    assert s.whatsapp_phone_number_id == "12345"
    assert s.whatsapp_verify_token == "veriftok"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest tests/test_settings.py -v`
Expected: FAIL — ImportError: cannot import name `Settings` from `settings`.

- [ ] **Step 3: Write minimal implementation**

Create `ai-service/settings.py`:

```python
import os


class Settings:
    def __init__(self) -> None:
        self.whatsapp_access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        self.whatsapp_phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        self.whatsapp_verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
        self.graph_base = "https://graph.facebook.com/v19.0/"


settings = Settings()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest tests/test_settings.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add ai-service/settings.py ai-service/tests/test_settings.py
git commit -m "feat(settings): add WhatsApp settings with env vars and defaults"
```

---

### Task 2: WhatsApp Graph API client

**Files:**
- Create: `ai-service/services/meta.py`
- Test: `ai-service/tests/test_meta.py`

**Interfaces:**
- Consumes: `services.meta` only (implicitly or through injected API key/functions). `requests` is mocked via monkeypatching in tests.
- Produces:
  - `send_message(phone_number_id: str, access_token: str, to: str, text: str) -> None` — POSTs a text message to `https://graph.facebook.com/v19.0/{phone_number_id}/messages`; raises `RuntimeError` on non-200 or network error.
  - `resolve_media_url(access_token: str, media_id: str) -> str` — GETs `https://graph.facebook.com/v19.0/{media_id}` and returns the `url` field.

- [ ] **Step 1: Write the failing test**

Create `ai-service/tests/test_meta.py`:

```python
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
    meta.send_message("12345", "tok", "2335566778", "Hello")

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
            raise requests.HTTPError("boom")

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

        raise_for_status = lambda self: None

    def fake_get(url, headers=None, timeout=None):
        return FakeResp()

    monkeypatch.setattr(meta.requests, "get", fake_get)
    url = meta.resolve_media_url("tok", "MEDIA1")
    assert url == "https://cdn.example/audio.ogg"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest tests/test_meta.py -v`
Expected: FAIL — `ModuleNotFoundError` / attribute error on `services.meta`.

- [ ] **Step 3: Write minimal implementation**

Create `ai-service/services/meta.py`:

```python
import requests

GRAPH_BASE = "https://graph.facebook.com/v19.0/"


def send_message(phone_number_id: str, access_token: str, to: str, text: str) -> None:
    url = f"{GRAPH_BASE}{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    try:
        resp = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=20,
        )
        resp.raise_for_status()
    except (requests.RequestException, requests.HTTPError) as exc:
        raise RuntimeError(f"WhatsApp send failed: {exc}") from exc


def resolve_media_url(access_token: str, media_id: str) -> str:
    url = f"{GRAPH_BASE}{media_id}"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json().get("url", "")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest tests/test_meta.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add ai-service/services/meta.py ai-service/tests/test_meta.py
git commit -m "feat(whatsapp): add Meta Graph API client for messages and media resolution"
```

---

### Task 3: Pydantic webhook request models

**Files:**
- Create: `ai-service/models.py` (modify — append models) — actually use a new file to avoid disturbing existing models.
- Create: `ai-service/models/webhook.py`
- Test: `ai-service/tests/test_webhook_models.py`

**Interfaces:**
- Consumes: nothing.
- Produces: Pydantic models in `models/webhook.py`:
  - `WebhookText(content: str)`
  - `WebhookAudio(id: str)`
  - `WebhookMessage(from: str, type: str, text: WebhookText | None = None, audio: WebhookAudio | None = None)`
  - `WebhookValue(messages: list[WebhookMessage] = [])`
  - `WebhookChange(value: WebhookValue)`
  - `WebhookEntry(changes: list[WebhookChange])`
  - `WebhookPayload(object: str, entry: list[WebhookEntry])`
  Behavior: `.text` and `.audio` are `None` when omitted; `.messages` defaults to `[]`.

- [ ] **Step 1: Write the failing test**

Create `ai-service/tests/test_webhook_models.py`:

```python
from models.webhook import WebhookPayload, WebhookMessage, WebhookAudio, WebhookText


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
    msg = payload.entry[0].changes[0].value.messages
    assert isinstance(msg, list)
    assert len(msg) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest tests/test_webhook_models.py -v`
Expected: FAIL — import error.

- [ ] **Step 3: Write minimal implementation**

Create `ai-service/models/webhook.py`:

```python
from pydantic import BaseModel, ConfigDict, Field


class WebhookText(BaseModel):
    body: str


class WebhookAudio(BaseModel):
    id: str


class WebhookMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: str = Field(alias="from")
    type: str
    text: WebhookText | None = None
    audio: WebhookAudio | None = None


class WebhookValue(BaseModel):
    messages: list[WebhookMessage] = []


class WebhookChange(BaseModel):
    value: WebhookValue


class WebhookEntry(BaseModel):
    changes: list[WebhookChange]


class WebhookPayload(BaseModel):
    object: str
    entry: list[WebhookEntry]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest tests/test_webhook_models.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add ai-service/models/webhook.py ai-service/tests/test_webhook_models.py
git commit -m "feat(webhook): add Pydantic models for Meta webhook payload"
```

---

### Task 4: In-process conversation memory

**Files:**
- Create: `ai-service/services/memory.py`
- Test: `ai-service/tests/test_memory.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `class Message(BaseModel)` with `role: str`, `content: str`.
  - `class MemoryStore` with `get(user_id: str) -> list[Message]`, `save(user_id: str, history: list[Message])`, `clear(user_id: str)`; caps history at last 20 entries.
  - `memory = MemoryStore()` — module-level singleton.

- [ ] **Step 1: Write the failing test**

Create `ai-service/tests/test_memory.py`:

```python
from services.memory import Message, MemoryStore


def test_save_get():
    m = MemoryStore()
    m.save("u1", [Message(role="user", content="hi")])
    hist = m.get("u1")
    assert len(hist) == 1
    assert hist[0].content == "hi"


def test_clear():
    m = MemoryStore()
    m.save("u1", [Message(role="user", content="hi")])
    m.clear("u1")
    assert m.get("u1") == []


def test_cap_at_20():
    m = MemoryStore()
    m.save("u1", [Message(role="user", content=f"m{i}") for i in range(25)])
    hist = m.get("u1")
    assert len(hist) == 20
    assert hist[0].content == "m5"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest tests/test_memory.py -v`
Expected: FAIL — import error.

- [ ] **Step 3: Write minimal implementation**

Create `ai-service/services/memory.py`:

```python
from threading import Lock

from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class MemoryStore:
    def __init__(self) -> None:
        self._store: dict[str, list[Message]] = {}
        self._lock = Lock()

    def get(self, user_id: str) -> list[Message]:
        with self._lock:
            return list(self._store.get(user_id, []))

    def save(self, user_id: str, history: list[Message]) -> None:
        with self._lock:
            truncated = history[-20:] if len(history) > 20 else history
            self._store[user_id] = list(truncated)

    def clear(self, user_id: str) -> None:
        with self._lock:
            self._store.pop(user_id, None)


memory = MemoryStore()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest tests/test_memory.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add ai-service/services/memory.py ai-service/tests/test_memory.py
git commit -m "feat(memory): add thread-safe in-process conversation history"
```

---

### Task 5: Webhook message orchestrator

**Files:**
- Create: `ai-service/services/webhook_handler.py`
- Create: `ai-service/services/pipeline.py` (light adapter exposing `process_text(message, phone) -> str` and `process_audio(text, phone) -> str`; wraps `ChatPipeline` and `transcribe`)
- Test: `ai-service/tests/test_webhook_handler.py`

**Interfaces:**
- Consumes:
  - `services.webhook_handler.WebhookHandler` constructed with a `processor` object having:
    - `handle_text(message: str, phone: str) -> str`
    - `handle_audio(audio_url: str, phone: str, access_token: str) -> str`
  - Send function: `services.meta.send_message(phone_number_id, access_token, to, text)`.
  - `settings` (for phone_number_id, access_token).
  - `memory` (for conversation history persistence).
- Produces:
  - `class WebhookHandler` with `.process(payload: WebhookPayload) -> None`:
    - nil if `payload.object != "whatsapp_business_account"`, no entry, no change, no messages.
    - For each message: route — `command(...)` for text commands; otherwise produce `user_text`; send a reply; persist `user_text` + reply to memory as user/assistant.
  - `_command(self, text, phone) -> str | None` — returns a reply string when `text` matches a command (`start`, `reset`, `start over`, `help`, `delete`), else None. `start` clears memory and returns greeting string; `reset`/`start over` clears memory and returns "Chat cleared…"; `help` returns the help menu; `delete` returns a deletion notice (no-op now).

- [ ] **Step 1: Write the failing test**

Create `ai-service/tests/test_webhook_handler.py`:

```python
from services.webhook_handler import WebhookHandler
from models.webhook import WebhookPayload, WebhookText


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
```

Test 1 — ignored payload:

```python
def test_non_whatsapp_object_is_ignored():
    sender = FakeSender()
    handler = WebhookHandler(processor=FakeProcessor(), sender=sender.send)
    payload = WebhookPayload(object="not_whatsapp", entry=[])
    handler.process(payload)
    assert sender.sent == []
```

Test 2 — text command start:

```python
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
```

Test 3 — text routed to processor:

```python
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
```

Test 4 — memory persisted:

```python
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
    from services.memory import memory, Message
    hist = memory.get("233556000000")
    assert hist[-2].role == "user"
    assert hist[-1].role == "assistant"
    memory.clear("233556000000")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest tests/test_webhook_handler.py -v`
Expected: FAIL — import error.

- [ ] **Step 3: Write minimal implementation**

Create `ai-service/services/webhook_handler.py`:

```python
from services.memory import Message, memory
from models.webhook import WebhookPayload


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

    def _dispatch(self, user_id, user_text, reply):
        self.sender(user_id, reply)
        self._save(user_id, user_text, reply)

    def _save(self, user_id, user_text, reply):
        history = memory.get(user_id)
        history.append(Message(role="user", content=user_text))
        history.append(Message(role="assistant", content=reply))
        memory.save(user_id, history)

    def _handle_message(self, msg):
        user_id = msg.from_
        if msg.type == "text" and msg.text:
            text = msg.text.body.strip()
            command_reply = self._command_reply(text, user_id)
            if command_reply is not None:
                self._save(user_id, text, command_reply)
                self.sender(user_id, command_reply)
                return
            reply = self.processor.handle_text(text, user_id)
            self._save(user_id, text, reply)
            self.sender(user_id, reply)
        elif msg.type == "audio" and msg.audio:
            # media resolution + transcription is deferred to the processor
            reply = self.processor.handle_audio(msg.audio.id, user_id)
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
```

Since the `Message` import is needed, `from services.memory import Message`. Add that to the imports.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest tests/test_webhook_handler.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add ai-service/services/webhook_handler.py ai-service/tests/test_webhook_handler.py
git commit -m "feat(webhook): add orchestrator handling commands and routing to processor"
```

---

### Task 6: Wire the webhook endpoints into main.py

**Files:**
- Modify: `ai-service/main.py`
- Test: `ai-service/tests/test_routes.py`

**Interfaces:**
- Consumes: `services.webhook_handler.WebhookHandler`, `services.meta`, `settings`, `models.webhook.WebhookPayload`, `services.transcribe.transcribe_from_audio_url`, `services.chat_pipeline.ChatPipeline`.
- Produces:
  - FastAPI routes `GET /webhook` and `POST /webhook`.
  - A `WebhookProcessor` adapter object that, given `(phone_number_id, access_token)`, wires:
    - `handle_text`: runs `ChatPipeline().run(<message>, PhoneNumber)` and returns `result["reply"]`.
    - `handle_audio`: runs `transcribe_from_audio_url(<audio_url>, access_token)` then the pipeline, returns the reply; on `RuntimeError` returns a friendly fallback string "Could not process the voice note. Please try again."
  - Also a module-level `webhook_handler = WebhookHandler(processor=..., sender=...)` in main.py, and `pipeline = ChatPipeline()` still.

- [ ] **Step 1: Write the failing test**

Create `ai-service/tests/test_webhook.py`:

```python
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
```

Note: The `client` fixture is defined at the top of the file, and `TestClient` comes from `fastapi.testclient` (`pip install httpx` may be required — add `httpx` to requirements if import fails). If the `from main import app` import triggers the DB/psycopg import chain, the `client` fixture still works since `ChatPipeline` is only instantiated lazily inside `_WebhookProcessor` (deferred). Verify `/health` as a baseline connectivity check.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest tests/test_webhook.py -v`
Expected: FAIL — no `GET /webhook` route yet.

- [ ] **Step 3: Write minimal implementation**

Modify `ai-service/main.py` to add:

At top, extend the FastAPI import to include `Request`, add `from fastapi.responses import Response`, and import `from models.webhook import WebhookPayload`, `from settings import settings`, `from services.webhook_handler import WebhookHandler`, and `from services import meta`.

Add helpers:

```python
def _verify_query(mode: str, verify_token: str, challenge: str) -> bool:
    return mode == "subscribe" and verify_token == settings.whatsapp_verify_token


class _WebhookProcessor:
    def __init__(self) -> None:
        self.pipeline = ChatPipeline()

    def handle_text(self, message: str, phone: str) -> str:
        result = self.pipeline.run(message=message, phone=phone)
        return result["reply"]

    def handle_audio(self, audio_id: str, phone: str) -> str:
        try:
            audio_url = meta.resolve_media_url(settings.whatsapp_access_token, audio_id)
            text, _lang = transcribe_from_audio_url(audio_url, access_token=settings.whatsapp_access_token)
            if not text:
                return "Could not transcribe the voice note. Please try again."
            result = self.pipeline.run(message=text, phone=phone)
            return result["reply"]
        except Exception:
            return "Could not process the voice note. Please try again."


def _send_whatsapp(to: str, text: str) -> None:
    try:
        meta.send_message(
            settings.whatsapp_phone_number_id,
            settings.whatsapp_access_token,
            to,
            text,
        )
    except RuntimeError:
        pass


webhook_handler = WebhookHandler(processor=_WebhookProcessor(), sender=_send_whatsapp)
```

Add routes:

```python
@app.get("/webhook")
def webhook_verify(
    hub_mode: str = "",
    hub_verify_token: str = "",
    hub_challenge: str = "",
):
    if _verify_query(hub_mode, hub_verify_token, hub_challenge):
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(content="Forbidden", status_code=403)


@app.post("/webhook")
async def webhook_receive(request: Request):
    raw = await request.json()
    payload = WebhookPayload.model_validate(raw)
    if payload.object == "whatsapp_business_account":
        webhook_handler.process(payload)
    return {"status": "ok"}
```

- [ ] **Step 4: Run test to verify it passes** — the verify handshake tests should pass.

- [ ] **Step 5: Run the full suite**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest`
Expected: All tests pass (previous tasks + new).

- [ ] **Step 6: Commit**

```bash
git add ai-service/main.py ai-service/tests/test_webhook.py
git commit -m "feat(webhook): expose GET /webhook verify and POST /webhook receive endpoints in FastAPI"
```

---

## Task 7: Remove deprecated Go and Node backends + document env

**Files:**
- Delete: `backend-go/` (entire directory)
- Delete: `backend/` (entire directory) — except preserve `backend/src/db/schema.sql`? The schema is referenced by the design doc. COPY `backend/src/db/schema.sql` into `ai-service/db/schema.sql` first.
- Modify: `ai-service/.env.example` (add WhatsApp vars)
- Test: `ai-service/tests/test_settings_export.py` (verify settings reads the new env names) — optional but include.

**Interfaces:**
- Consumes: settings env vars.
- Produces: enriched `.env.example` with:
```
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
```
- A preserved database schema at `ai-service/db/schema.sql`.

- [ ] **Step 1: Preserve the DB schema**

Copy `backend/src/db/schema.sql` → `ai-service/db/schema.sql` (create dir).

- [ ] **Step 2: Add WhatsApp env vars to .env.example**

Edit `ai-service/.env.example` to add the three WHATSAPP vars (empty) after `DATABASE_URL=`.

- [ ] **Step 3: Delete deprecated backends**

Run PowerShell:
```powershell
Remove-Item -Recurse -Force backend-go
Remove-Item -Recurse -Force backend
```

- [ ] **Step 4: Verify nothing references backend**

Run: `grep -R "backend-go"` (via `Get-ChildItem`) — expect none.

- [ ] **Step 5: Run full suite**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest`
Expected: all pass.

- [ ] **Step 6: Update README project structure and tech stack (optional but recommended)**

Replace Go references with the consolidated FastAPI service. (Do this lightly; the README will be fully rewritten in a docs pass.)

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore: remove deprecated Go and Node backends; consolidate env and schema into ai-service"
```

---

## Self-Review

**Spec coverage:** The webhook consolidation issue (#2) is fully covered: Meta verify (GET /webhook), message receive (POST /webhook), text commands, voice note media resolution + transcription, reply send, conversation memory, and removal of deprecated Go/Node backends. In-flight features like signature verification, Celery queue, and idempotency are explicitly out of scope (later issues).

**Placeholder scan:** None remaining. Task 6 defines concrete `_WebhookProcessor` with `handle_text`/`handle_audio`, `_send_whatsapp`, and the `webhook_handler` instance — no forward references. Task 3's `WebhookMessage` uses `Field(alias="from")` + `ConfigDict(populate_by_name=True)` so `msg.from_` parses the JSON key `from` correctly.

**Type consistency:** `WebhookHandler(processor, sender=...)` — processor has `.handle_text(message, phone)` and `.handle_audio(audio_id, phone)`. Sender has `.send(to, text)` → satisfied by `lambda to, text: ...` from `meta.send_message`. `WebhookMessage.from_` due to Pydantic alias. Verify serialization with `populate_by_name`.

**Meds/?? — verify end-to-end: WebhookHandler._command_reply is a pure function fresh each process so it can be tested; the processor/sender are injected and the handler never imports the pipeline/Groq/log in Task 5. Good isolation.

**Gap:** Task 5 Step 1 Fallback: the `audo` handler calls `self.processor.handle_audio(msg.audio.id, user_id)` — the actual media. Fine.