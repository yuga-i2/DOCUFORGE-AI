"""
DocuForge AI — Celery Worker Configuration

Configures the Celery application for background agent task execution.
Task results are stored in Redis via Upstash. All long-running agent
pipelines are dispatched as Celery tasks to avoid blocking the API.
"""

import logging
import os
from celery import Celery

logger = logging.getLogger(__name__)

celery_app = Celery(
    "docuforge",
    broker=os.getenv("UPSTASH_REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("UPSTASH_REDIS_URL", "redis://localhost:6379/0"),
    include=["api.workers.analysis_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(name="api.workers.analysis_tasks.run_analysis_pipeline")
def run_analysis_pipeline(file_path: str, query: str, session_id: str) -> dict:
    """Wrapper task to make run_analysis_pipeline callable by Celery."""
    from api.workers.analysis_tasks import run_analysis_pipeline as _run_pipeline
    return _run_pipeline(file_path, query, session_id)
