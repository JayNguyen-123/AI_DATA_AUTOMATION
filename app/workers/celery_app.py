from celery import Celery
from app.config import settings

# Initialize the main Celery orchestration instance
celery_app = Celery(
    "automation_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Production configuration for concurrency and safety
celery_app.conf.update(
    task_track_started=True,
    task_acks_late=True,              # Task is acknowledge only AFTER successful execution
    worker_prefetch_multiplier=1,     # Worker takes 1 task at a time to prevent backlog skew
    worker_max_tasks_per_child=100,   # Restart worker thread periodically to prevent memory leaks
    include=["app.workers.tasks"]     # Explicitly register the tasks module
)
