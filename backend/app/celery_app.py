from celery import Celery
from app.config import settings

celery_app = Celery("gmail_bill_scanner", broker=settings.REDIS_URL)
celery_app.conf.update(
    result_backend=settings.REDIS_URL,
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

# Ensure tasks are imported to register them with Celery
import app.tasks
