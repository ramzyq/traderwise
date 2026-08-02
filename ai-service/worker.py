from celery_app import app
from tasks import process_webhook  # ensures the task is registered

if __name__ == "__main__":
    app.worker_main()