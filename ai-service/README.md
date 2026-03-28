# TraderWise AI Service

FastAPI service for transcription and chat reasoning.

## Setup

```bash
cd ai-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --port 8000
```

## Endpoints

- `GET /health`
- `POST /chat`
- `POST /transcribe`
- `POST /test`

## Quick Test

```bash
curl -X POST http://localhost:8000/test -H "Content-Type: application/json" -d "{\"message\":\"I want to restock tomorrow\",\"phone\":\"test\"}"
```
