from celery import Celery
from app.config import settings

celery_app = Celery("gmail_bill_scanner", broker=settings.REDIS_URL)
celery_app.conf.result_backend = None

import app.tasks
