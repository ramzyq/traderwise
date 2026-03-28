# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

TraderWise is a WhatsApp AI business co-pilot for Ghanaian informal market traders. Traders send voice notes in Twi; the system transcribes, translates, reasons via Claude, and replies in under 10 seconds.

CBC Hackathon • University of Ghana • Track 3: Economic Empowerment

---

## Monorepo Structure

Two services, two team members:

```
traderwise/
├── backend/        # Node.js + Express — webhook gateway + React dashboard (Julien)
└── ai-service/     # Python + FastAPI — AI pipeline (Richmond)
```

The only integration point between services:
- `POST /chat` — text message in → Claude response out
- `POST /transcribe` — Twilio audio URL in → transcription text out

---

## AI Service — Python FastAPI (Richmond)

### Setup & Run

```bash
cd ai-service
python -m venv venv && source venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

### Test the pipeline without WhatsApp

```bash
curl -X POST http://localhost:8000/test \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to restock tomorrow but not sure how much to buy", "phone": "test"}'
```

### Environment variables

```
ANTHROPIC_API_KEY=      # Claude API (claude-sonnet-4-6)
OPENAI_API_KEY=         # Whisper speech-to-text
GOOGLE_TRANSLATE_KEY=   # Google Translate API (Twi ↔ English)
DATABASE_URL=           # Supabase PostgreSQL — shared by Julien at Hour 0
```

---

## Backend Service — Node.js (Julien)

```bash
cd backend
npm install && cp .env.example .env
npm run dev     # nodemon dev server
npm test        # run tests
```

---

## Message Flow Architecture

```
Trader sends WhatsApp voice note
  → Twilio webhook → Node.js /webhook
  → POST audio_url to Python /transcribe
      → Whisper API → transcription
      → language detection
      → Google Translate (Twi → English if needed)
  → POST text to Python /chat
      → distress classifier  ← runs first; if triggered, bypass Claude entirely
      → fraud pattern check  ← if triggered, return safety protocol
      → load trader profile from PostgreSQL
      → assemble system prompt (role + profile + last 3 interactions)
      → Claude API (claude-sonnet-4-6)
      → response validator (post-process → re-call Claude only if hard violation)
      → Google Translate (English → Twi if needed)
  → Twilio reply → trader's WhatsApp
```

---

## Key Design Rules (Enforced in Code)

**Claude plays "Ama"** — a trusted Makola market trader. The system prompt in `ai-service/prompts/system_prompt.py` is the core product artifact.

**Claude never gives direct recommendations.** Every response must apply the 4-lens framework (Cash Flow / Risk / Relationships / Learning), avoid "you should", and end with a question returning agency to the trader.

**Response validator: post-process first, re-call second.** String-replace "you should" → "one thing to consider"; append a closing `?` if missing. Only re-call Claude if the response contains an explicit directive ("I recommend", "You must"). Re-calling on every failure adds 3–5s of latency.

**Distress classifier runs before Claude on every message.** Twi distress phrases (`mensu adwene`) are included. If triggered: bypass Claude, send human acknowledgment, log separately.

**Audio is never persisted.** Download to `tempfile`, pass to Whisper, delete immediately. No external storage service.

---

## Database (Supabase PostgreSQL)

Three tables — schema in `backend/src/db/schema.sql`:
- `traders` — one row per phone number; stores `language`, `goods_type[]`, `market`, `working_cap`, `susu_day`
- `interactions` — every message + response; includes `distress_flag`, `fraud_flag`, `transcription`, `claude_input`, `claude_output`, `final_reply`
- `credit_customers` — per-trader credit ledger with `amount_owed`

---

## Build Timeline (4 Hours)

| Hour | Richmond (AI Service) | Julien (Backend) | Done When |
|------|----------------------|-----------------|-----------|
| 0–1 | FastAPI skeleton + raw Claude API call | Node.js + Express + `/webhook` logging Twilio POSTs | Both servers run locally. First Twilio message received and logged. |
| 1–2 | `/chat` endpoint + system prompt v1 (Ama persona, 4-lens, constraints) + trader profile injection | Connect Express `/webhook` → Richmond's `/chat`. Return Claude reply via Twilio TwiML. | End-to-end: WhatsApp text in → Claude reply back in WhatsApp. |
| 2–3 | Whisper `/transcribe` endpoint + Google Translate pipeline (Twi ↔ English) | Detect text vs audio in webhook. Pass audio URL to `/transcribe` before `/chat`. | WhatsApp voice note in Twi → Twi reply received. |
| 3–4 | Distress classifier + fraud pattern recognizer + response validator | PostgreSQL tables created (Supabase). Save interactions. Load last 3 for context. | All 5 QA scenarios pass. Distress bypasses Claude. Fraud protocol fires. Demo rehearsed once. |

## QA: Five Scenarios That Must Pass by Hour 4

Every Claude response must use the 4-lens framework, avoid direct recommendations, and end with a question:

1. **Spoilage-Credit Dilemma** — tomatoes going bad, customer wants GHS 200 credit
2. **Restocking Decision** — how much to buy Thursday before a busy Friday
3. **Fraud Alert** — stranger demands GHS 500 for a "new market license"
4. **Sunday Check-In** — three weekly reflection questions, synthesize one insight
5. **Distress Signal** — "mensu adwene, borrowed from moneylender" → classifier fires, Claude bypassed

---

## Iron Rule

No new features after Hour 4. After that: bug fixes, response quality tuning, and demo rehearsal only.
