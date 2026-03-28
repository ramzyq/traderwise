import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from models import ChatRequest, ChatResponse, TranscribeRequest, TranscribeResponse
from services.chat_pipeline import ChatPipeline
from services.transcribe import transcribe_from_audio_url

load_dotenv()

app = FastAPI(title="TraderWise AI Service", version="0.1.0")
pipeline = ChatPipeline()


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "ai-service"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = pipeline.run(message=request.message, phone=request.phone)
        return ChatResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chat pipeline failed: {exc}") from exc


@app.post("/transcribe", response_model=TranscribeResponse)
def transcribe(request: TranscribeRequest) -> TranscribeResponse:
    try:
        text, language = transcribe_from_audio_url(request.audio_url)
        return TranscribeResponse(text=text, language=language)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}") from exc


@app.post("/test", response_model=ChatResponse)
def test_chat(request: ChatRequest) -> ChatResponse:
    return chat(request)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
