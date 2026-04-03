from celery import Celery
from agent_aichain.core.config import settings

celery_app = Celery(
    "agent_aichain",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Import tasks after celery_app is defined to register task decorators
from . import tasks  # noqa