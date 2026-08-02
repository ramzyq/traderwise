import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import Response

from models import ChatRequest, ChatResponse, TranscribeRequest, TranscribeResponse
from models.webhook import WebhookPayload
from services import meta
from services.chat_pipeline import ChatPipeline
from services.transcribe import transcribe_from_audio_url
from services.webhook_handler import WebhookHandler
from settings import settings

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
        text, language = transcribe_from_audio_url(request.audio_url, access_token=request.access_token)
        return TranscribeResponse(text=text, language=language)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}") from exc


@app.post("/test", response_model=ChatResponse)
def test_chat(request: ChatRequest) -> ChatResponse:
    return chat(request)


def _verify_query(mode: str, verify_token: str, challenge: str) -> bool:
    return mode == "subscribe" and verify_token == settings.whatsapp_verify_token


class _WebhookProcessor:
    def handle_text(self, message: str, phone: str) -> str:
        result = pipeline.run(message=message, phone=phone)
        return result["reply"]

    def handle_audio(self, audio_id: str, phone: str) -> str:
        try:
            audio_url = meta.resolve_media_url(settings.whatsapp_access_token, audio_id)
            text, _lang = transcribe_from_audio_url(audio_url, access_token=settings.whatsapp_access_token)
            if not text:
                return "Could not transcribe the voice note. Please try again."
            result = pipeline.run(message=text, phone=phone)
            return result["reply"]
        except Exception:
            return "Could not process the voice note. Please try again."


def _send_whatsapp(to: str, text: str) -> None:
    try:
        meta.send_message(
            settings.whatsapp_phone_number_id,
            settings.whatsapp_access_token,
            to,
            text,
        )
    except RuntimeError:
        pass


webhook_handler = WebhookHandler(processor=_WebhookProcessor(), sender=_send_whatsapp)


@app.get("/webhook")
def webhook_verify(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
):
    if _verify_query(hub_mode, hub_verify_token, hub_challenge):
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(content="Forbidden", status_code=403)


@app.post("/webhook")
async def webhook_receive(request: Request):
    raw = await request.json()
    payload = WebhookPayload.model_validate(raw)
    if payload.object == "whatsapp_business_account":
        webhook_handler.process(payload)
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
