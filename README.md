# 🛒 TraderWise

> **Voice-First Business Co-Pilot for Ghana's Informal Market Traders.**

TraderWise is a WhatsApp AI business co-pilot for traders in Ghana's informal
markets (Makola, Kejetia, Agbogbloshie). Traders send a voice note in Twi; the
system transcribes, translates, reasons through Claude, and replies on WhatsApp
in seconds — never by deciding for them, but by helping them decide better.

**Built for Ghana. Powered by AI. Grounded in Makola.**
CBC Hackathon • University of Ghana • Track 3: Economic Empowerment

---

## Table of Contents

- [Why TraderWise](#why-traderwise)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Getting Started (Local)](#getting-started-local)
- [Environment Variables](#environment-variables)
- [Production Deployment](#production-deployment)
- [Testing](#testing)
- [Design Principles](#design-principles)
- [Ethics Architecture](#ethics-architecture)
- [Business Model](#business-model)
- [License](#license)

---

## Why TraderWise

Every morning over 100,000 traders in Ghana's markets wake up to make decisions
that decide whether their families eat that week: how much stock to buy, who to
extend credit to, how to price, how to avoid spoilage. They make these
decisions **alone**, with no tools and no thinking partner.

**TraderWise is the business partner they never had access to — until now.**

In under 8 seconds, a trader sends a WhatsApp voice note in Twi and receives a
contextual, thoughtful response that helps her think through — not decides for
her.

The goal: **reduce weekly spoilage loss for informal traders by 5%.** At 500
traders, that is **GHS 75,000** returned to families that earned it.

---

## How It Works

### The Voice Pipeline

```
Trader sends WhatsApp voice note (Twi / Ga)
  → WhatsApp Cloud API → FastAPI webhook (signature-verified, BSUID-aware)
  → Celery task queue (Redis broker) → worker
      → Audio: media ID → /transcribe → Whisper/Groq ASR → text + language
      → Text: pass through
      → Distress classifier + fraud checker (run BEFORE Claude — no reasoning LLM)
      → Load trader profile + last interactions → build system prompt (Ama persona)
      → LLM reasoning (pluggable: Claude / Groq / OpenAI)
      → Response validator (post-process → re-call only on hard violation)
      → Translate back to Twi if needed
  → WhatsApp reply (via Graph API, supports BSUID recipients)
```

### The Trader Context Profile

TraderWise builds a memory layer per trader over time — no forms to fill out.
Claude asks one question per weekly check-in until the profile is rich enough to
give genuinely useful, personalized support.

```json
{
  "trader_id": "TW-GH-00847",
  "name": "Ama",
  "market": "Makola Section C",
  "goods_type": ["tomatoes", "peppers", "onions"],
  "typical_working_capital": 800,
  "susu_day": "Friday",
  "language": "twi"
}
```

---

## Architecture

The repository is a **single consolidated Python service** (`ai-service/`). It
hosts the FastAPI webhook gateway, the AI pipeline, and a Celery background
worker, and deploys to Railway or Render.

- **Web + worker** — FastAPI serves `/webhook`, `/health`, `/chat`,
  `/transcribe`, `/test`. A Celery worker (Redis broker) consumes incoming
  **webhook** messages so the gateway returns `200 OK` immediately and heavy
  AI work happens asynchronously.
- **Webhooks** — Meta message signatures are verified with
  `X-Hub-Signature-256`. Sender identity is resolved from either the classic
  `"from": <phone>` field **or** the newer Meta **BSUID** (Business-Scoped User
  ID, `"from_user_id": "GH.xxx"`) rollout; replies are sent to BSUIDs via the
  `recipient` Graph API field.
- **DB — Supabase PostgreSQL**; automatic **SQLite fallback** for local dev.
- **Idempotent interactions** — duplicate webhooks (same message ID) are
  skipped so at-least-once delivery never double-computes a reply.

---

## Project Structure

```
traderwise/
├── README.md                     ← this file
├── railway.json / render.yaml    ← PaaS deployment config
├── docs/superpowers/             ← design specs & implementation plans
└── ai-service/
    ├── main.py                   ← FastAPI app: webhook, health, chat, transcribe
    ├── worker.py / celery_app.py ← Celery worker & queue wiring
    ├── tasks.py                  ← process_webhook / run_webhook_pipeline
    ├── settings.py               ← env schema + production startup validation
    ├── models/                   ← Pydantic webhook models (BSUID-aware)
    ├── services/
    │   ├── webhook_handler.py    ← routes messages → commands / pipeline
    │   ├── chat_pipeline.py       ← main reasoning orchestrator
    │   ├── transcribe.py          ← Whisper/Groq speech-to-text
    │   ├── translate.py           ← Twi ↔ English (Khaya or Google)
    │   ├── meta.py                ← WhatsApp Graph API send (BSUID-aware)
    │   ├── distress.py / fraud.py ← pre-LLM classifiers (bypasses Claude)
    │   ├── validator.py           ← response post-processor
    │   ├── memory.py              ← per-trader conversation memory
    │   ├── signature.py           ← Meta webhook signature verify
    │   ├── db.py                  ← PostgreSQL + SQLite fallback
    │   └── llm/                   ← pluggable providers (claude / groq / openai)
    ├── prompts/system_prompt.py   ← Ama persona + 4-lens framework
    ├── tests/                     ← pytest suite
    ├── Dockerfile / Procfile
    ├── requirements.txt
    └── .env.example
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Messaging** | WhatsApp Business Cloud API (Meta) |
| **Webhook gateway** | Python FastAPI (single consolidated service) |
| **Async queue** | Celery + Redis broker |
| **Speech-to-Text** | Groq Whisper (`whisper-large-v3-turbo`) |
| **Reasoning (LLM)** | Pluggable: Claude (default) · Groq · OpenAI |
| **Translation** | Khaya (default) · Google Translate (Twi ↔ English) |
| **Database** | Supabase PostgreSQL (SQLite local fallback) |
| **Deploy** | Docker · Railway · Render (web + worker) |

---

## Getting Started (Local)

### Prerequisites

- Python 3.11+
- A Meta WhatsApp Business Cloud API account
- ngrok (for local webhook tunneling)
- Redis (only if running the Celery worker; optional for single-process dev)

### Setup & Run

```powershell
cd ai-service
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# fill in your keys
uvicorn main:app --reload --port 8000
```

### Expose the webhook (local dev)

```powershell
ngrok http 8000 --request-header-add "ngrok-skip-browser-warning:true"
```

Set the ngrok HTTPS URL + `/webhook` as your Meta callback URL, and use
`ngrok-skip-browser-warning` if needed.

### Quick pipeline test (no WhatsApp needed)

```bash
curl -X POST http://localhost:8000/test \
  -H "Content-Type: application/json" \
  -d '{"message":"I want to restock tomorrow, but not sure how much to buy","phone":"test"}'
```

---

## Environment Variables

**`ai-service/.env`** — full reference (see `.env.example`):

```bash
APP_ENV=development
PORT=8000

# LLM reasoning
GROQ_API_KEY=
# Pick LLM provider: groq | claude | openai ; default groq

# Speech-to-text
ASR_PROVIDER=groq          # or khaya
ASR_LANGUAGE=tw            # source language

# Translation
TRANSLATION_PROVIDER=khaya # or google

# WhatsApp
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_APP_SECRET=

# Data
DATABASE_URL=              # Supabase Postgres; falls back to SQLite if unset

# Celery (worker)
BROKER_URL=
RESULT_BACKEND=redis://localhost:6379/0
```

> In `production` mode, `APP_ENV=production`, the service validates at startup
> that `GROQ_API_KEY`, `WHATSAPP_*`, `DATABASE_URL`, and `BROKER_URL` are set
> and fails fast if any are missing.

---

## Production Deployment

The service ships with Docker and PaaS configs.

### Docker

```bash
cd ai-service
docker build -t traderwise . --config=1
docker run -p 8000:8000 --env-file .env traderwise
```

### Railway

`railway.json` builds from `ai-service/Dockerfile`. Set env vars in the Railway
dashboard; the start command runs `uvicorn main:app --port $PORT`.

### Render

`render.yaml` declares two services sharing `ai-service/Dockerfile`:

- `traderwise-ai` — web service running uvicorn (health check on `/health`)
- `traderwise-worker` — worker running `celery -A worker worker --loglevel=info`

Both require `BROKER_URL`, `RESULT_BACKEND`, the WhatsApp vars, Groq key, and
`DATABASE_URL` to be set in the dashboard (`sync: false`).

---

## Testing

```bash
cd ai-service
pytest              # or: python -m pytest
```

The suite covers webhook models (classic `from` **and** BSUID `from_bb_uid`),
webhook handler routing, signature verification, transcription, translation,
ASR/translations, classifiers, memory, DB idempotency, Meta send behavior
(phone vs. BSUID recipient), and LLM provider fallbacks.

---

## Design Principles

- **Claude plays "Ama"** — a trusted Makola market trader
  (`prompts/system_prompt.py`). This is the core product artifact.
- **No direct recommendations.** Every response applies the **4-lens framework**
  (Cash Flow / Risk / Relationships / Learning), avoids "you should", and ends
  with a question returning agency to the trader.
- **Classifiers come before the LLM.** Distress and fraud recognition run
  first and can bypass Claude entirely.
- **Audio is never persisted** — downloaded to `tempfile`, as turned to text,
  then deleted.
- **BSUID-ready** — the system parses Meta's new Business-Scoped Username
  rollout (`from_bb_uid`) and routes replies via the `recipient` field.

---

## Ethics Architecture

Ethics is a design feature, not a disclaimer.

1. **Agency Preservation — the AI never decides.** Responses end with a
   question back to the trader; Claude restructures problems, builds better
   questions, and the trader stays the decision-maker.
2. **Data Minimalism.** We collect goods type, market, weekly patterns, and
   token. We do **not** collect full names, NIA numbers, exact location, or
   income. Audio is deleted immediately; traders can send `DELETE ME` to
   permanently erase their data.
3. **No upselling, no referral incentives.** The system prompt prohibits
   recommending specific financial products or loans. MFI partners receive
   anonymized aggregate data only — never individual profiles.
4. **Distress Protocol.** A classifier runs on every message (Twi + English +
   Ga) before Claude. If a distress signal fires, business mode is paused and
   the trader is acknowledged as a human first.
5. **The Dependency Test — build to become unnecessary.** A graduation check
   runs periodically; when a trader's decisions show consistent soundness, the
   app steps back. A tool that makes itself unnecessary is a trustworthy tool.

---

## Business Model

| Stream | Description |
|--------|-------------|
| **B2B (Primary)** | MFIs pay GHS 500–2,000/month for anonymized aggregate market intelligence |
| **B2C (Secondary)** | Free tier (10 check-ins/month) • Premium GHS 5/month via MoMo |
| **Grants** | Tony Elumelu Foundation, GIZ, MasterCard Foundation, USAID/Ghana |

---

## License

MIT — see [LICENSE](LICENSE).

---

*TraderWise isn't an app. It's the business partner Ama never had access to — until now.*