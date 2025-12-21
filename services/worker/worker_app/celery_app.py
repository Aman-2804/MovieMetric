"""
Celery application configuration
"""
import os
from celery.schedules import crontab
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Celery app
celery_app = Celery(
    "moviemetric_worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"),
    include=[
        "services.worker.worker_app.tasks_ingest",
        "services.worker.worker_app.tasks_compute",
        "services.worker.worker_app.tasks_search",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Celery Beat schedule configuration
    beat_schedule={
        # Nightly ingest - runs at 2 AM UTC daily
        "nightly-ingest": {
            "task": "ingest.run_full",
            "schedule": crontab(hour=2, minute=0),
            "options": {"expires": 3600},  # Expire after 1 hour if not picked up
        },
        # Nightly trending compute - runs at 3 AM UTC daily
        "nightly-trending-compute": {
            "task": "compute.trending",
            "schedule": crontab(hour=3, minute=0),
            "options": {"expires": 3600},
        },
        # Nightly genre stats compute - runs at 3:15 AM UTC daily
        "nightly-genre-stats-compute": {
            "task": "compute.genre_stats",
            "schedule": crontab(hour=3, minute=15),
            "options": {"expires": 3600},
        },
        # Weekly search index rebuild - runs every Monday at 4 AM UTC
        "weekly-search-index-rebuild": {
            "task": "search.update_index",
            "schedule": crontab(hour=4, minute=0, day_of_week=1),  # Monday = 1
            "options": {"expires": 7200},  # Expire after 2 hours
        },
        # Weekly recommendations recompute - runs every Monday at 5 AM UTC
        "weekly-recommendations-recompute": {
            "task": "compute.recommendations",
            "schedule": crontab(hour=5, minute=0, day_of_week=1),  # Monday = 1
            "options": {"expires": 10800},  # Expire after 3 hours (recommendations can take time)
        },
    },
)

