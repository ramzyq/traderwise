from celery_app import app
from models.webhook import WebhookPayload


def build_webhook_handler():
    from main import webhook_handler

    return webhook_handler


def run_webhook_pipeline(payload_dict: dict) -> None:
    try:
        payload = WebhookPayload.model_validate(payload_dict)
    except Exception:
        return None
    if payload.object != "whatsapp_business_account" or not payload.entry:
        return None
    build_webhook_handler().process(payload)
    return None


@app.task(name="traderwise.process_webhook")
def process_webhook(payload_dict: dict) -> None:
    run_webhook_pipeline(payload_dict)