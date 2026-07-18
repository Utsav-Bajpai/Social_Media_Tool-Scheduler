"""
The actual Celery task that runs at (or after) a post's scheduled time.

Handles the Draft -> Scheduled -> Publishing -> Published/Failed status
lifecycle from the project spec, plus retry-with-backoff on failure.
"""
import asyncio

from celery import shared_task
from celery.utils.log import get_task_logger

import publisher
import scheduler_storage

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    # Exponential backoff: 10s, 20s, 40s between attempts
    retry_backoff=10,
    retry_backoff_max=120,
    retry_jitter=True,
)
def publish_post_task(self, post_id: str, platform: str, draft: str, user_id: str):
    attempt = self.request.retries + 1
    logger.info(f"Publishing post {post_id} to {platform} (attempt {attempt})")
    scheduler_storage.update_status(post_id, status="publishing", attempts=attempt)

    try:
        result = asyncio.run(publisher.publish_post(platform, draft, user_id))
    except Exception as exc:
        is_final_attempt = attempt > self.max_retries
        if is_final_attempt:
            scheduler_storage.update_status(
                post_id, status="failed", attempts=attempt, error=str(exc)
            )
            logger.error(f"Post {post_id} permanently failed after {attempt} attempts: {exc}")
            raise
        # Not final yet: mark it back to "scheduled" (queued for retry) and
        # let Celery's built-in backoff schedule the next attempt.
        scheduler_storage.update_status(
            post_id, status="scheduled", attempts=attempt, error=str(exc)
        )
        raise self.retry(exc=exc)

    scheduler_storage.update_status(post_id, status="published", attempts=attempt)
    logger.info(f"Post {post_id} published: {result}")
    return result
