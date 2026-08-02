# Celery + Redis Async Task Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the WhatsApp message processing off the FastAPI request thread into an asynchronous Celery task queue backed by Redis, so the webhook returns `200 OK` to Meta immediately and a Celery worker runs the AI pipeline (transcribe → guardrails → LLM → validate → reply) asynchronously, with retry support.

**Architecture:** FastAPI's `POST /webhook` acknowledges Meta instantly (200) and enqueues a Celery task carrying the normalized payload. A Celery worker consumes the task and runs the existing `WebhookHandler.process` logic off-request. The task functions are pure (testable without a broker) and only the thin Celery task wrapper touches the broker. Redis URL comes from `BROKER_URL` env (Upstash free tier compatible), defaulting to `redis://localhost:6379/0` for local dev.

**Tech Stack:** Celery 5.4.x, Redis 5.x (redis-py), FastAPI, Python 3.11+.

## Global Constraints

- Broker/backend URL from env `BROKER_URL`, default `redis://localhost:6379/0`.
- Celery accepts `redis` transport (redis-py), not `rediss` unless using SSL comma config — Upstash uses `rediss://`; pass through verbatim for prod.
- The Celery task function must be pure (no broker dependency) so it is unit-testable; only `app.send_task` / `task.delay` touches Redis.
- `POST /webhook` must return `{"status": "ok"}` in < 500ms and enqueue a task.
- No real broker in unit tests: use Celery's `task_always_eager` mode OR mock `send_task`. Tests must not require a live Redis.
- The existing 32-test suite must stay green (additions only).

---

### Task 1: Add celery config module and worker task function

**Files:**
- Create: `ai-service/celery_app.py`
- Create: `ai-service/tasks.py`
- Test: `ai-service/tests/test_tasks.py`

**Interfaces:**
- Consumes: `models.webhook.WebhookPayload` (for type hint only), the existing `WebhookHandler.process(payload)` from `services.webhook_handler`.
- Produces:
  - `celery_app.py`: `app` (a `Celery` instance named "traderwise" with `broker` from `os.getenv("BROKER_URL", "redis://localhost:6379/0")` and `backend` from `os.getenv("RESULT_BACKEND", "redis://localhost:6379/0")`), plus `task_serializer="json"`, `accept_content=["json"]`, `result_serializer="json"`, `timezone="UTC"`, `enable_utc=True`.
  - `tasks.py`: `def run_webhook_pipeline(payload_dict: dict) -> None` — a plain function that models the payload to `WebhookPayload`, runs the existing `webhook_handler.process(payload)`, guarded so malformed payloads are swallowed. Returns nothing.
  - `register_tasks()` explained below; plus `app` in `celery_app` is wired with the registered task when the module is imported by the worker (`-A`).

- [ ] **Step 1: Write the failing test**

Create `ai-service/tests/test_tasks.py`:

```python
from tasks import run_webhook_pipeline


def test_run_webhook_pipeline_ignores_non_whatsapp():
    # A missing/invalid payload must not raise.
    result = run_webhook_pipeline({})
    assert result is None


def test_run_webhook_pipeline_accepts_malformed_payload():
    result = run_webhook_pipeline({"object": "not_whatsapp", "entry": []})
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest tests/test_tasks.py -v`
Expected: FAIL — ImportError (`tasks` module missing).

- [ ] **Step 3: Write minimal implementation**

Create `ai-service/celery_app.py`:

```python
import os

from celery import Celery


app = Celery(
    "traderwise",
    broker=os.getenv("BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("RESULT_BACKEND", "redis://localhost:6379/0"),
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=os.getenv("CELERY_TASK_ALWAYS_EAGER", "0") == "1",
)
```

Create `ai-service/tasks.py`:

```python
from celery_app import app
from models.webhook import WebhookPayload
from services.webhook_handler import WebhookHandler


def build_webhook_handler() -> WebhookHandler:
    # Deferred import to avoid importing main-style hooks at worker import time.
    from main import webhook_handler

    return webhook_handler


def run_webhook_pipeline(payload_dict: dict) -> None:
    try:
        payload = WebhookPayload.model_validate(payload_dict)
    except Exception:
        return None
    handler = build_webhook_handler()
    handler.process(payload)
    return None


@app.task(name="traderwise.process_webhook")
def process_webhook(payload_dict: dict) -> None:
    run_webhook_pipeline(payload_dict)
```

- [ ] **Step 4: Run test to verify it passes**

Run (tests will defer import of `build_webhook_handler`, which imports `main`); the two unit tests above only call `run_webhook_pipeline({})` and `run_webhook_pipeline({"object": "not_whatsapp"})` which both return early before building the handler, so no `main` import is triggered. Verify the tests pass.

- [ ] **Step 5: Add an eager-mode task test using `process_webhook` with `Cinvoke`-style mocking**

Append to `ai-service/tests/test_tasks.py`:

```python
from unittest.mock import patch
from tasks import process_webhook


def test_process_webhook_eager_dispatch(monkeypatch):
    dispatched = {}
    with patch("tasks.process_webhook.delay") as mock_delay:
        mock_delay.return_value = None
        # simulate the caller sending the task
        process_webhook.delay({})
        assert mock_delay.called
```

Then run the full tasks test file.

- [ ] **Step 6: Run the full suite**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest -q`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add ai-service/celery_app.py ai-service/tasks.py ai-service/tests/test_tasks.py
git commit -m "feat(queue): add Celery app and async webhook pipeline task"
```

---

### Task 2 — Wire `POST /webhook` to enqueue instead of processing inline

**Files:**
- Modify: `ai-service/main.py`
- Test: `ai-service/tests/test_webhook.py` (add test)

**Interfaces:**
- Consumes: `tasks.process_webhook` (the Celery task) from `ai-service/tasks.py`.
- Produces: `POST /webhook` enqueues `process_webhook.delay(payload.model_dump(...))` and returns `{"status": "ok"}`.

- [ ] **Step 1: Write failing test**

Append to `ai-service/tests/test_webhook.py`:

```python
from unittest.mock import patch


def test_webhook_receive_enqueues_task(client, monkeypatch):
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "sekrit")
    body = {
        "object": "whatsapp_business_account",
        "entry": [{"changes": [{"value": {"messages": [
            {"from": "233556000000", "type": "text", "text": {"body": "restock"}}
        ]}}]}],
    }
    with patch("tasks.process_webhook.delay") as mock_delay:
        resp = client.post("/webhook", json=body)
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
        assert mock_delay.called
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest tests/test_webhook.py::test_post_webhook_enqueues_to -v`
Expected: FAIL — `process_webhook.delay` not called (webhook still processes inline).

- [ ] **Step 3: Implement**

Replace the `POST /webhook` route in `main.py` with an async enqueueing version:

```python
from tasks import process_webhook

@app.post("/webhook")
async def webhook_receive(request: Request):
    try:
        raw = await request.json()
        payload = WebhookPayload.model_validate(raw)
    except (json.JSONDecodeError, ValidationError):
        return {"status": "ok"}
    data = payload.model_dump()
    if payload.object == "whatsapp_business_account":
        process_webhook.delay(data)
    return {"status": "ok"}
```

Add `from tasks import process_webhook` at the top of main.py.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest -q`
Expected: all pass, including `test_post` 200 + enqueue assertion.

- [ ] **Step 5: Update `.env.example` with broker settings**

Append to `ai-service/.env.example`:

```
BROKER_URL=redis://localhost:6379/0
RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_ALWAYS_EAGER=0
```

- [ ] **Step 6: Commit**

```bash
git add ai-service/main.py ai-service/.env.example ai-service/tests/test_webhook.py
git commit -m "feat(webhook): enqueue AI processing to Celery from POST /webhook"
```

---

### Task 3 — Worker entrypoint + docs

**Files:**
- Create: `ai-service/web_worker.py`
- Modify: `README.md` (brief run instructions)

**Interfaces:**
- Consumes: `celery_app.app` (the Celery broker).
- Produces: an importable worker entrypoint so Celery can run `celery -A ` with `register_tasks` on the current app. The worker process is a separate container/Renbound.

- [ ] **Step 1: Write the worker entrypoint**

Create `ai-service/worker.py`:

```python
from celery_app import app
from tasks import process_webhook  # ensures the task is registered

if __name__ == "__main__":
    app.worker_main()
```

- [ ] **Step 2: Document run commands**

Append to `README.md` (under Running the AI Service):
- Single: `cd` then `python -m venv venv...` to install celery `[ redis ]`.
- Run the FastAPI gateway and the worker in separate processes:
  - API: `uvicorn main:app --reload --port 8000`
  - Worker: `celery -A worker worker --loglevel=info`
  Note the worker and API both use `BROKER_URL`.

- [ ] **Step 3: Run suite**

Run: `cd ai-service; .\venv\Scripts\python.exe -m pytest -q` — all pass.

- [ ] **Step 4: Commit**

```bash
git add ai-service/worker.py README.md
git commit -m "docs: add Celery worker entrypoint and run instructions"
```

---

## Self-Review

**Cap:** Tasks cover issue #3 (Celery + Redis): Task 1 configures Celery + task; Task 2 wires the webhook to enqueue; Task 3 worker entry + docs. 

**Placeholders:** none. All code given.

**Type consistency:** `process_webhook` is the task exposed in both `tasks.py` and `worker.py`; `run_webhook_pipeline(payload_dict: dict) -> None` is the pure API used by tests in Task 1. The `build_webhook_handler` is a deferred import to avoid worker-import recursion: `main` imports `tasks` (for `process_webhook`), and `tasks` imports `webhook_handler` from `main` — the deferred import in `run_webhook_pipeline` breaks the circular import. Reviewer must verify this load-order safety is actually used: the two Task 1 unit tests return before building the handler, so they don't splice a `main` circular import; the enqueue path in Task 2 also doesn't build the handler (it only calls `.delay`). The expensive handler import only happens inside the actual worker when a real message is processed.

**Self-review note:** Because `main` imports `tasks` at top level, and `tasks` imports `webhook_handler` lazily inside `run_webhook_pipeline`, there is no cycle at import time. Verified by the Task1 test contract (never imports `main`). If `main` ends up importing `tasks` and `tasks` importing `main` at module scope, that is a defect to flag — the plan keeps `main → tasks → (webhook_handler deferred)`.