from celery_app import app
from models.webhook import WebhookPayload
from services.db import update_interaction_status


def build_webhook_handler():
    from main import webhook_handler

    return webhook_handler


def _message_ids(payload: WebhookPayload):
    for entry in payload.entry:
        for change in entry.changes:
            for msg in change.value.messages:
                if msg.id:
                    yield msg.id


def run_webhook_pipeline(payload_dict: dict) -> None:
    try:
        payload = WebhookPayload.model_validate(payload_dict)
    except Exception:
        return None
    if payload.object != "whatsapp_business_account" or not payload.entry:
        return None
    message_ids = list(_message_ids(payload))
    try:
        build_webhook_handler().process(payload)
    except Exception:
        for mid in message_ids:
            update_interaction_status(mid, "failed")
        raise
    return None


@app.task(name="traderwise.process_webhook")
def process_webhook(payload_dict: dict) -> None:
    run_webhook_pipeline(payload_dict)