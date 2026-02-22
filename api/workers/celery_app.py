"""
DocuForge AI — Celery Worker Configuration

Configures the Celery application for background agent task execution.
Supports both local Redis (redis://) and Upstash hosted Redis (rediss://)
with automatic SSL detection. All credentials are read from environment.
"""

import logging
import os
import re
import ssl
from celery import Celery
from dotenv import load_dotenv

# Load environment variables from .env file FIRST, before any getenv calls
load_dotenv()

logger = logging.getLogger(__name__)


def _mask_redis_url(url: str) -> str:
    """
    Mask the password in a Redis URL for safe logging.
    Replaces the password portion with *** to prevent credential exposure.
    
    Args:
        url: Redis connection URL
        
    Returns:
        URL with password masked
    """
    return re.sub(r":([^@]+)@", ":***@", url)


def _build_celery_app() -> Celery:
    """
    Build and configure the Celery application with automatic Redis SSL detection.
    Reads broker URL from UPSTASH_REDIS_URL environment variable, falling back
    to localhost Redis if not set.
    
    Returns:
        Configured Celery application instance
    """
    redis_url = os.getenv("UPSTASH_REDIS_URL", "redis://localhost:6379/0")

    if not os.getenv("UPSTASH_REDIS_URL"):
        logger.warning(
            "UPSTASH_REDIS_URL not set — falling back to redis://localhost:6379/0"
        )

    logger.info("Celery broker: %s", _mask_redis_url(redis_url))

    app = Celery(
        "docuforge",
        broker=redis_url,
        backend=redis_url,
        include=["api.workers.analysis_tasks"],
    )

    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        broker_connection_retry_on_startup=True,
        broker_connection_max_retries=3,
    )

    if redis_url.startswith("rediss://"):
        logger.info("Upstash SSL detected — configuring Redis SSL with CERT_NONE")
        app.conf.update(
            broker_use_ssl={
                "ssl_cert_reqs": ssl.CERT_NONE,
                "ssl_check_hostname": False,
            },
            redis_backend_use_ssl={
                "ssl_cert_reqs": ssl.CERT_NONE,
                "ssl_check_hostname": False,
            },
        )

    return app


celery_app = _build_celery_app()
