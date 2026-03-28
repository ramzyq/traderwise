from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    reply: str
    distress_flag: bool = False
    fraud_flag: bool = False


class TranscribeRequest(BaseModel):
    audio_url: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    access_token: str | None = None  # Required for WhatsApp Cloud API media URLs


class TranscribeResponse(BaseModel):
    text: str
    language: str = "unknown"
