# 🛒 TraderWise

> *Voice-First Business Intelligence Co-Pilot for Ghana's Informal Market Traders*

**Built for Ghana. Powered by Claude. Grounded in Makola.**

CBC Hackathon • University of Ghana • Track 3: Economic Empowerment

---

## What is TraderWise?

Every morning, over 100,000 traders in Ghana's markets — Makola, Kejetia, Agbogbloshie — wake up and make decisions that determine whether their families eat that week. They decide how much stock to buy, who to extend credit to, how to price against competitors, and how to avoid spoilage losses. They make these decisions alone, with no tools, and no thinking partner.

**TraderWise is the business partner they never had access to — until now.**

Traders send a WhatsApp voice note in Twi. In under 8 seconds, they get a contextual, thoughtful response that helps them think through their decision — not one that decides for them.

---

## How It Works

### The 7-Step Voice Pipeline

```
1. Trader sends WhatsApp voice note (OGG/OPUS) in Twi
2. Meta webhook → Go server receives the message
3. Audio media ID resolved → Go calls Python /transcribe
4. Groq Whisper (whisper-large-v3-turbo) → transcription + language detection
5. If Twi: Google Translate → English for Claude processing
6. Distress classifier + fraud checker run before Claude
7. English input + trader profile → Claude API (Ama persona, 4-lens framework)
8. Response validated → translated back to Twi if needed → WhatsApp reply
```

### The Trader Context Profile

TraderWise builds a memory layer for each trader over time — no forms to fill out. Claude asks one question per weekly check-in until the profile is rich enough to give genuinely useful, personalized support.

```json
{
  "trader_id": "TW-GH-00847",
  "name": "Afia",
  "market": "Makola Section C",
  "goods_type": ["tomatoes", "peppers", "onions"],
  "typical_working_capital": 800,
  "susu_day": "Friday",
  "credit_customers": [
    { "name": "Maame Ama", "owed": 120 }
  ],
  "weekly_patterns": {
    "high_demand_days": ["Friday", "Saturday"],
    "typical_margin_percent": 22,
    "avg_spoilage_loss_weekly": 35
  },
  "language": "twi"
}
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Messaging** | WhatsApp Business API (Meta Cloud API) |
| **Webhook Server** | Go + net/http |
| **AI Pipeline** | Python + FastAPI |
| **Speech-to-Text** | Groq Whisper (whisper-large-v3-turbo) |
| **Reasoning** | Claude API (claude-sonnet-4-6) — Ama persona |
| **Translation** | Google Translate API (Twi ↔ English) |
| **Database** | Supabase PostgreSQL • SQLite fallback for local dev |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Go 1.22+
- A Meta WhatsApp Business API account
- ngrok (for local webhook tunneling)

### Running the AI Service

```bash
cd ai-service
python -m venv venv && source venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
uvicorn main:app --reload --port 8000
```

### Running the Go Webhook Server

```bash
cd backend-go
go mod tidy
go run main.go
```

### Exposing the Webhook (local dev)

```bash
ngrok http 3000 --request-header-add "ngrok-skip-browser-warning:true"
```

Set the ngrok HTTPS URL as your Meta webhook callback URL with `/webhook` appended.

### Environment Variables

**`ai-service/.env`**
```bash
ANTHROPIC_API_KEY=        # Claude API (claude-sonnet-4-6)
GROQ_API_KEY=             # Groq Whisper speech-to-text
GOOGLE_TRANSLATE_KEY=     # Google Translate (Twi ↔ English)
DATABASE_URL=             # Supabase PostgreSQL — falls back to SQLite if not set
PORT=8000
```

**`backend-go/.env`**
```bash
PORT=3000
AI_SERVICE_URL=http://localhost:8000
WHATSAPP_ACCESS_TOKEN=    # Meta WhatsApp access token (refreshes every 24h in dev)
WHATSAPP_PHONE_NUMBER_ID= # Meta phone number ID
WHATSAPP_VERIFY_TOKEN=    # Your chosen webhook verify token
```

### WhatsApp Commands

| Command | Action |
|---------|--------|
| `start` | Welcome message + begin session |
| `reset` | Clear conversation history |
| `help`  | Show available commands |

---

## Project Structure

```
traderwise/
├── ai-service/                        # Python FastAPI — AI pipeline
│   ├── main.py                        # FastAPI app — /chat, /transcribe, /test
│   ├── models.py                      # Pydantic request/response models
│   ├── requirements.txt
│   ├── .env.example
│   ├── prompts/
│   │   └── system_prompt.py           # Ama persona + 4-lens framework
│   └── services/
│       ├── chat_pipeline.py           # Main pipeline orchestrator
│       ├── claude_client.py           # Anthropic API client
│       ├── distress.py                # Distress classifier (bypasses Claude)
│       ├── fraud.py                   # Fraud pattern recognizer
│       ├── validator.py               # Response post-processor
│       ├── transcribe.py              # Groq Whisper speech-to-text
│       ├── translate.py               # Google Translate (Twi ↔ English)
│       └── db.py                      # PostgreSQL + SQLite fallback
│
├── backend-go/                        # Go — WhatsApp webhook server
│   ├── main.go                        # HTTP server + route setup
│   ├── go.mod
│   ├── handlers/
│   │   └── webhook.go                 # Meta webhook verify + message handler
│   └── services/
│       ├── ai.go                      # Calls Python AI service
│       ├── whatsapp.go                # Sends replies via Meta Graph API
│       └── memory.go                  # In-memory conversation history
│
└── backend/                           # Node.js (reference — superseded by Go)
    └── src/
        └── db/
            └── schema.sql             # PostgreSQL schema (traders, interactions, credit_customers)
```

---

## Ethics Architecture

TraderWise treats ethics as a design feature, not a disclaimer.

### ① Agency Preservation — Claude Never Decides
Every response is validated to ensure it ends with a question back to the trader. Claude restructures problems and asks better questions. The trader is always the decision-maker.

### ② Data Minimalism
We collect goods type, market, weekly patterns, and credit relationships. We do **not** collect full names, NIA numbers, exact location, or income level. Audio files are deleted within 24 hours. Traders can send `DELETE ME` to permanently erase all their data.

### ③ No Upselling, No Referral Incentives
The system prompt explicitly prohibits recommending specific financial products or loans. MFI partners receive anonymized aggregate data only — never individual trader profiles.

### ④ Distress Protocol
A classifier runs on every message before Claude processes it, watching for distress signals in Twi and English. If detected: business mode is paused, and the trader is acknowledged as a human first.

### ⑤ The Dependency Test — Build to Become Unnecessary
Every 90 days, a graduation check runs. If a trader's decision patterns show consistently sound choices, the app tells her she's learned well and may not need to check in as often. A tool that tries to make itself unnecessary is a trustworthy tool.

---

## Sample Interaction

**🎙️ Afia's voice note (Twi):**
> *"Ama, me tomatoes bi reba bad. Ɛyɛ 2 days more. Maame Esi wants to take GHS 200 worth but she says she'll pay next week. Me sika mu reba down. Meyɛ dɛn?"*

**🤖 TraderWise response (Twi, ~8 seconds later):**
> *"Afia, mekye wo asɛm no. Ɛyɛ decision a ɛyɛ den. Tomatoes a ɛreba bad — sɛ wonntu no nnɛ, wobehu sika biara? Daabi. Enti credit no nyɛ sɛ wode sika ma no — ɛyɛ sɛ wode tomatoes a wobesei de kyɛ no. Asɛm a ɛho hia: Maame Esi — wabɔ wo ka pɛn da bi?"*

Notice: Claude never says give her the credit or don't. It restructures the problem and gives Afia a better question to answer herself.

---

## Business Model

| Stream | Description |
|--------|-------------|
| **B2B (Primary)** | MFIs pay GHS 500–2,000/month for anonymized aggregate market intelligence |
| **B2C (Secondary)** | Free tier (10 check-ins/month) • Premium GHS 5/month via MoMo |
| **Grants** | Tony Elumelu Foundation, GIZ, MasterCard Foundation, USAID/Ghana |

---

## Hackathon Context

Built at the **CBC Hackathon, University of Ghana** under **Track 3: Economic Empowerment**.

The goal: reduce weekly spoilage loss for informal traders by 5%. At 500 traders, that's GHS 75,000 returned to families that earned it.

---

## License

MIT — see [LICENSE](LICENSE)

---

*TraderWise isn't an app. It's the business partner Afia never had access to — until now.*
