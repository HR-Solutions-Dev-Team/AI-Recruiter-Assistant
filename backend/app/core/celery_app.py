"""
Celery application configuration.
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "ai_recruiter",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.matching_tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # 9 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,
)

# Task routes
celery_app.conf.task_routes = {
    "app.tasks.matching_tasks.*": {"queue": "matching"},
}
