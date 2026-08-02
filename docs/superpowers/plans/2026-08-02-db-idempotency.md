# Supabase Idempotency + State Tracking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers  — subagent-driven-development or executing-plans. Steps use checkbox (`- [ ]`).

**Goal (Issue #7):** Connect Supabase PostgreSQL and implement message deduplication (idempotency) plus interaction state tracking (`pending`, `completed`, `failed`) for WhatsApp interactions.

## Acceptance Criteria
- [ ] Database migration script for `traders`, `interactions`, `credit_customers`.
- [ ] Idempotency check using Meta WhatsApp message ID to ignore duplicate webhook triggers.
- [ ] Interaction state updated as Celery worker processes the pipeline.

## Design

The message flow after Issue #3 (Celery): `POST /webhook` → `process_webhook.delay(payload)` → worker → `run_webhook_pipeline` → `WebhookHandler.process(payload)` → `_handle_message(msg)` → `processor.handle_text/handle_audio` → `pipeline.run` → `save_interaction`.

Meta sends each WhatsApp message with a stable `id` on the message object. We use it to dedupe: if an interaction row already exists for that `meta_message_id`, the webhook delivery is a duplicate and is ignored.

### Schema changes (both Postgres `db/schema.sql` and SQLite fallback)

Add two columns to `interactions`:
- `meta_message_id text` — Meta WhatsApp message ID (unique when non-null).
- `status text not null default 'pending'` — lifecycle: `pending` → `completed` | `failed`.

`incoming_message` already exists but save_interaction does not set it (only claude_input). We keep usage minimal to avoid regressions.

### Files

- Modify: `ai-service/db/schema.sql` — Postgres migration (add `meta_message_id` + `status`).
- Modify: `ai-service/services/db.py` — SQLite schema + new/updated functions.
- Add: `ai-service/db/migrate.sql` or keep schema.sql as the migration (decision: schema.sql is the migration; add `IF NOT EXISTS ADD COLUMN` guarded style).
- Modify: `ai-service/models/webhook.py` — add `id` field to `WebhookMessage` (Meta message id).
- Modify: `ai-service/services/webhook_handler.py` — pass `msg.id` through to processor + do a pending/completed state update around processing.
- Modify: `ai-service/services/chat_pipeline.py` — accept optional `message_id`; pass to `save_interaction`.
- Tests: `ai-service/tests/test_db.py` (new), extend `test_webhook_handler.py`.

---

### Task 1 — WebhookMessage.id and WebhookHandler threading

`models/webhook.py`: add `id` to `WebhookMessage` (required, like Meta sends):
```python
class WebhookMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    from_: str = Field(alias="from")
    type: str
    text: WebhookText | None = None
    audio: WebhookAudio | None = None
```

Keep backward-compatible: make `id` optional `id: str | None = None` to avoid breaking existing tests that post messages without an id (test_webhook.py posts without `id`). So use `id: str | None = None`.

**webhook_handler.py `_handle_message`** — for each text/audio message, before processing, call a db idempotency check via the processor. To avoid importing db constraints into the handler, we extend `WebhookHandler.process` to skip known `meta_message_id`s:

Introduce in db a `message_co` helper returns existence; handler calls it to dedupe.

**Local JSONStore state queue** — the worker already uses Celery; early `status=pending` is written when the task starts (before processing), Completed/failed written after.

---

## Deliberate scope

The project uses a dual-db (Postgres-first, SQLite-fallback) pattern in `db.py`. To keep tests deterministic and free of a live Postgres/Supabase, all new logic must be testable against SQLite (the fallback path is the CI-tested one). The Postgres path mirrors it.

### Functions to add/change in `services/db.py`

Present add-on:

```python
def message_exists(meta_message_id: str | None) -> bool:
    """Idempotency check: has this Meta message id already been recorded?"""
    if not meta_message_id:
        return False
    # PG path: SELECT EXISTS ... ; SQLite fallback same
    ...

def save_interaction(..., meta_message_id=None, status="pending", ...) -> None:
    # insert new row with status; on conflict (meta_message_id unique) do NOT re-insert
    ...

def update_interaction_status(meta_message_id: str, status: str) -> None:
    # UPDATE interactions SET status=%s WHERE meta_message_id=%s
    ...
```

Idempotency rule applied in `webhook_handler.process`:
- For each message: if `save (get exists)` returns True → it is a duplicate → skip sending and skip re-processing. Otherwise → mark pending row, process, mark completed (or failed on exception).

Implementation note: choose simple + safe: a `mark`-front/`complete`-back around the processor in the handler. A transient failure in the worker → status stays `pending` or becomes `failed`.

---

## Self-Review

- Key naming/segue consistent with `meta_message_id` (WhatsApp field `id`).
- Status enum `pending`/`completed`/`failed` matches Issue #7.
- Test over SQLite fallback (no Supabase needed in CI).
- `save_interaction` signature extended backward-compatibly (new optional kwargs, default `status="pending"`).
- No webhook-format break: WebhookMessage.id optional.