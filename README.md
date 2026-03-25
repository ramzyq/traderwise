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
2. WhatsApp webhook receives the audio file
3. Audio → OpenAI Whisper API (speech-to-text, Twi-capable)
4. Transcription → Language detection module
5. Twi → English translation for Claude processing
6. English input + trader context profile → Claude API (reasoning engine)
7. Claude response → translated back to Twi → WhatsApp reply
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
| **Frontend** | WhatsApp Business API (Meta Cloud API) • SMS fallback via Hubtel |
| **Backend** | Node.js + Express • PostgreSQL • Redis • Bull Queue |
| **AI Pipeline** | OpenAI Whisper (speech-to-text) • Claude API (reasoning) • Helsinki-NLP / Google Translate (Twi translation) |
| **Infrastructure** | Railway / Render • Supabase • Cloudflare R2 (audio storage) |
| **Stretch Goal** | ElevenLabs TTS for voice responses back to trader |

---

## Getting Started

### Prerequisites

- Node.js v18+
- PostgreSQL
- Redis
- A WhatsApp Business API account (or Twilio sandbox for development)

### Installation

```bash
git clone https://github.com/ramzyq/traderwise.git
cd traderwise
npm install
cp .env.example .env
# Fill in your API keys in .env
npm run dev
```

### Environment Variables

```bash
ANTHROPIC_API_KEY=        # Claude API
OPENAI_API_KEY=           # Whisper speech-to-text
WHATSAPP_TOKEN=           # WhatsApp Business API token
WHATSAPP_VERIFY_TOKEN=    # Webhook verification token
DATABASE_URL=             # PostgreSQL connection string
REDIS_URL=                # Redis connection string
R2_BUCKET_URL=            # Cloudflare R2 for audio storage
```

---

## Project Structure

```
trader-wise/
├── src/
│   ├── index.js                  # Entry point / Express server
│   ├── webhooks/
│   │   └── whatsapp.js           # WhatsApp incoming message handler
│   ├── pipeline/
│   │   ├── transcribe.js         # Whisper speech-to-text
│   │   ├── translate.js          # Twi ↔ English translation
│   │   └── respond.js            # Claude API call + response builder
│   ├── modules/
│   │   ├── distressDetector.js   # Safety classifier (runs before Claude)
│   │   ├── fraudAlert.js         # Fraud pattern recognition
│   │   └── checkin.js            # Sunday weekly check-in scheduler
│   ├── db/
│   │   ├── traderProfile.js      # CRUD for trader profiles
│   │   └── schema.sql            # PostgreSQL schema
│   ├── prompts/
│   │   └── systemPrompt.js       # Claude system prompt builder
│   └── utils/
│       ├── queue.js              # Bull Queue for async audio processing
│       └── storage.js            # Cloudflare R2 audio file handling
├── tests/
│   └── scenarios/                # Real trader scenarios for testing
├── docs/
│   ├── architecture.md
│   ├── ethics.md
│   └── demo-script.md
├── .env.example
└── README.md
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
