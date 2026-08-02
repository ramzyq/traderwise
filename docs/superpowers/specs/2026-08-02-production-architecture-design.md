# Production Architecture Design: TraderWise (Zero-Cost Student Stack)

**Date:** 2026-08-02  
**Status:** Approved  
**Target Platform:** WhatsApp Business Cloud API (Meta)  
**Cost Profile:** 100% Free Tier Services (Groq, Khaya AI / Ghana NLP, Supabase, Upstash Redis)

---

## 1. Executive Summary

TraderWise is a voice-first business co-pilot for Ghanaian informal market traders. This production design refactors the codebase from a multi-language prototype (Go webhook + Node.js backend + Python AI service) into a unified, single-service Python (FastAPI) asynchronous backend architecture.

The system supports voice notes and text in **Twi**, **Ga**, and **English**, utilizing Khaya AI (Ghana NLP) and Groq for Speech-to-Text (ASR) and Translation, paired with Groq (Llama 3.3 70B) for high-speed, zero-cost AI reasoning under the "Ama" market trader persona.

---

## 2. System Architecture & Component Consolidation

### 2.1 Consolidated Architecture Overview

```
[Trader via WhatsApp] 
        │
        ▼ (Webhook HTTP POST)
[FastAPI Gateway]  ──(Verify Meta Signature & Validate Payload)──► Return 200 OK (< 500ms)
        │
        ▼ (Enqueue Job)
[Upstash Redis Queue]
        │
        ▼ (Poll Task)
[Celery Worker Service]
        ├── 1. Download Media (WhatsApp Graph API)
        ├── 2. ASR Speech-to-Text (Groq Whisper / Khaya ASR)
        ├── 3. Guardrails Check (Ga, Twi, English Distress & Fraud Detectors)
        ├── 4. Translation Layer (Khaya AI / Google Translate -> English)
        ├── 5. Profile & History Load (Supabase PostgreSQL)
        ├── 6. Reasoning Engine (Groq Llama 3.3 70B via Pluggable Client)
        ├── 7. Response Validation & Post-Processing (Ama persona & 4-lens rule)
        ├── 8. Back-Translation (English -> Ga / Twi)
        └── 9. Send WhatsApp Reply (Meta Graph API) & Save Interaction to DB
```

### 2.2 Deprecation Strategy
- `backend/` (Node.js Express) and `backend-go/` (Go) are marked deprecated/removed.
- All webhook handling, verification, media resolution, and task queue management are consolidated into the Python service under `ai-service/` (to be renamed or structured as `app/`).

---

## 3. Technology Stack & Zero-Cost Infrastructure

| Layer | Provider / Tool | Cost Profile | Role |
|-------|-----------------|--------------|------|
| **Web Gateway** | Python FastAPI + Uvicorn | Free / Self-hosted | Webhook receipt, signature validation, async task dispatch |
| **Task Queue** | Celery + Upstash Redis | Free Tier (10k requests/day) | Background execution of AI voice pipeline |
| **Speech-to-Text (ASR)** | Groq Whisper-large-v3-turbo & Khaya ASR | Free Tier | Audio transcription for English, Twi, and Ga |
| **Translation** | Khaya AI API (Ghana NLP) | Free Developer Tier | Bidirectional translation: `tw` ↔ `en` and `ga` ↔ `en` |
| **LLM Reasoning** | Groq API (`llama-3.3-70b-versatile`) | Free Tier | Core reasoning engine playing the "Ama" persona |
| **Database** | Supabase PostgreSQL | Free Tier (500MB DB) | Persistent storage for traders, interactions, and credit ledgers |
| **Deployment** | Render / Railway / Fly.io | Free Tier | Hosting FastAPI gateway and Celery worker processes |

---

## 4. Pluggable Provider Interface

To ensure portability and future-proofing, the AI pipeline uses abstract provider interfaces:

```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_message: str) -> str:
        pass

class ASRProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_bytes: bytes) -> tuple[str, str]: # (text, language)
        pass

class TranslationProvider(ABC):
    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        pass
```

Environment variable switching:
- `LLM_PROVIDER=groq` (Default: `llama-3.3-70b-versatile`), supports switching to `claude` or `openai`.
- `ASR_PROVIDER=groq` (Fallback: `khaya`).
- `TRANSLATION_PROVIDER=khaya` (Fallback: `google`).

---

## 5. Multilingual & Guardrails Pipeline (Twi, Ga, English)

### 5.1 Distress & Fraud Detectors
Before reasoning, safety check algorithms run across English, Twi, and Ga keywords.

- **Twi Distress Phrases:** `mensu adwene`, `mepɛ sɛ mewu`, `sika no asa`
- **Ga Distress Phrases:** `mijɔɔɔ`, `kɛmɔ mi gbee`, `shika bɛ`
- **English Distress Phrases:** `I want to give up`, `no money left`, `in deep trouble`

If triggered: Bypass LLM reasoning, trigger human empathetic acknowledgment, save flag in database, and alert support if configured.

### 5.2 Ama Persona & 4-Lens Framework
The prompt enforces that the AI operates as **Ama**, a seasoned Makola market trader:
- **4 Lenses:** Cash Flow, Risk, Relationships, Learning.
- **Constraints:** Never give direct directives ("You should", "You must").
- **Mandatory Ending:** Always end with a clarifying/agency question back to the trader.

---

## 6. Database Schema (Supabase PostgreSQL)

Schema maintained in Supabase PostgreSQL:

1. `traders`
   - `id` (UUID, PK)
   - `phone` (VARCHAR UNIQUE, indexed)
   - `name` (VARCHAR)
   - `market` (VARCHAR)
   - `language` (VARCHAR: `twi`, `ga`, `english`)
   - `goods_type` (TEXT[])
   - `working_capital` (NUMERIC)
   - `susu_day` (VARCHAR)
   - `created_at` (TIMESTAMPTZ)

2. `interactions`
   - `id` (UUID, PK)
   - `trader_phone` (VARCHAR, FK -> traders.phone)
   - `status` (VARCHAR: `pending`, `completed`, `failed`)
   - `media_id` (VARCHAR)
   - `transcription` (TEXT)
   - `detected_language` (VARCHAR)
   - `english_input` (TEXT)
   - `llm_output` (TEXT)
   - `final_reply` (TEXT)
   - `distress_flag` (BOOLEAN)
   - `fraud_flag` (BOOLEAN)
   - `latency_ms` (INTEGER)
   - `created_at` (TIMESTAMPTZ)

3. `credit_customers`
   - `id` (UUID, PK)
   - `trader_phone` (VARCHAR, FK -> traders.phone)
   - `customer_name` (VARCHAR)
   - `amount_owed` (NUMERIC)
   - `updated_at` (TIMESTAMPTZ)

---

## 7. Verification & Self-Review Check

- **Placeholder Scan:** No TBD or TODO items remaining.
- **Internal Consistency:** All services route through Celery + Redis back to Meta Graph API.
- **Scope Check:** Fully cohesive, covers end-to-end webhook to WhatsApp reply flow.
- **Ambiguity Check:** Explicit provider interface and fallback logic defined.
