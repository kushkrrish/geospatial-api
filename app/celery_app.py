from celery import Celery

from app.config.config import settings


celery_app = Celery(
    "geospatial_file_api",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.tasks"
    ]
)


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    task_track_started=True,

    broker_connection_retry_on_startup=True,
)