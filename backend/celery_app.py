"""
Celery app for the Auto-Posting scheduler.

Broker/result backend is Redis (Upstash in production — Upstash exposes a
standard Redis-protocol URL, so this needs zero Upstash-specific code).
Run the worker separately from the API process:

    celery -A celery_app worker --loglevel=info --pool=solo   # Windows
    celery -A celery_app worker --loglevel=info                # Mac/Linux

The API process (uvicorn) only *enqueues* jobs; this worker is what
actually executes them at their scheduled time.
"""
import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "scheduler",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    # Upstash (and most managed Redis) requires TLS on port 6380 — rediss://
    # URLs need this so Celery's SSL handshake doesn't get rejected.
    broker_use_ssl={"ssl_cert_reqs": "none"} if REDIS_URL.startswith("rediss://") else None,
    redis_backend_use_ssl={"ssl_cert_reqs": "none"} if REDIS_URL.startswith("rediss://") else None,
)

# Import tasks so Celery registers them when the app is loaded
import scheduler_tasks  # noqa: E402,F401
