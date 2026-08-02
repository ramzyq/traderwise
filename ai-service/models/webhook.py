from pydantic import BaseModel, ConfigDict, Field


class WebhookText(BaseModel):
    body: str


class WebhookAudio(BaseModel):
    id: str


class WebhookMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    from_: str = Field(alias="from")
    type: str
    text: WebhookText | None = None
    audio: WebhookAudio | None = None


class WebhookValue(BaseModel):
    messages: list[WebhookMessage] = []


class WebhookChange(BaseModel):
    value: WebhookValue


class WebhookEntry(BaseModel):
    changes: list[WebhookChange]


class WebhookPayload(BaseModel):
    object: str
    entry: list[WebhookEntry]