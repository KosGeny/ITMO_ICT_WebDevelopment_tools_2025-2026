import os
from dotenv import load_dotenv

from celery import Celery

load_dotenv()

celery_app = Celery(
    "task_manager",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"),
    include=["app.celery_tasks"],
)

celery_app.conf.update(
    task_track_started=True,

    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    timezone="UTC",
    enable_utc=True,

    result_expires=7200,

    broker_connection_retry_on_startup=True,
)