from tasks import process_webhook, run_webhook_pipeline


def test_run_webhook_pipeline_ignores_empty_payload():
    assert run_webhook_pipeline({}) is None


def test_run_webhook_pipeline_ignores_non_whatsapp():
    assert run_webhook_pipeline({"object": "not_whatsapp", "entry": []}) is None


def test_process_webhook_registered_on_app():
    assert process_webhook.name == "traderwise.process_webhook"
    assert process_webhook.name in process_webhook.app.tasks