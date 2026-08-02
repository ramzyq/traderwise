import os

from celery import Celery

app = Celery(
    "traderwise",
    broker=os.getenv("BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("RESULT_BACKEND", "redis://localhost:6379/0"),
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=os.getenv("CELERY_TASK_ALWAYS_EAGER", "0") == "1",
)