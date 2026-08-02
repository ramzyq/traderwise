# TraderWise AI Service

The consolidated Python service powering [TraderWise](../README.md) — a WhatsApp
AI business co-pilot for Ghana's informal market traders.

This single FastAPI service hosts the webhook gateway, the AI pipeline, and the
Celery background worker. See the [repository README](../README.md) for the full
product overview, architecture, deployment, and environment variable reference.

## Setup

```bash
cd ai-service
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --port 8000
```

## Run the Celery worker (for async webhook processing)

```bash
celery -A worker worker --loglevel=info
```

## Endpoints

| Method | Path          | Purpose |
|--------|---------------|---------|
| GET    | `/health`     | Liveness probe |
| POST   | `/chat`       | Text in → Claude response out |
| POST   | `/transcribe` | Twilio/WhatsApp audio URL → transcription text out |
| POST   | `/test`       | Pipeline smoke test without WhatsApp |
| GET    | `/webhook`    | Meta webhook verification (hub.challenge) |
| POST   | `/webhook`    | Meta webhook delivery → enqueues Celery task |

## Quick Test

```bash
curl -X POST http://localhost:8000/test \
  -H "Content-Type: application/json" \
  -d '{"message":"I want to restock tomorrow, but not sure how much to buy","phone":"test"}'
```

## Tests

```bash
pytest
```

See the [repository root](../README.md) for the full production deployment
guide (Docker, Railway, Render) and the ethics architecture.