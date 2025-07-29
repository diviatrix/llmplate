"""Celery application configuration."""
from celery import Celery
from kombu import Exchange, Queue

from app.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "llm_template_backend",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.generation.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,  # Results expire after 1 hour
    task_track_started=True,
    task_time_limit=3600,  # Hard time limit of 1 hour
    task_soft_time_limit=3300,  # Soft time limit of 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routing
celery_app.conf.task_routes = {
    "app.generation.tasks.*": {"queue": "generation"},
    "app.export.tasks.*": {"queue": "export"},
}

# Queue configuration
celery_app.conf.task_queues = (
    Queue("default", Exchange("default"), routing_key="default"),
    Queue("generation", Exchange("generation"), routing_key="generation"),
    Queue("export", Exchange("export"), routing_key="export"),
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-generations": {
        "task": "app.generation.tasks.cleanup_old_generations",
        "schedule": 3600.0,  # Run every hour
    },
    "update-model-prices": {
        "task": "app.providers.tasks.update_model_prices",
        "schedule": 86400.0,  # Run once per day
    },
}