"""
Publishes a post to a platform.

Right now this SIMULATES publishing — no real X/LinkedIn/Meta API calls
are made. It's written as its own module with one clear function so the
Platform Connections + Auto-Posting teams can drop in real API calls here
later without touching the scheduler, retry logic, or status tracking at
all. Same pattern as storage.py's Supabase/in-memory swap.

To go live later: replace the body of `publish_post` with real calls
(e.g. requests to the X API using the stored OAuth token for this
account), and raise an exception on failure — the Celery task already
retries on any exception, so no other code needs to change.
"""
import asyncio
import os
import random

SIMULATE_FAILURE_RATE = float(os.getenv("SIMULATE_FAILURE_RATE", "0.15"))


async def publish_post(platform: str, draft: str, user_id: str) -> dict:
    """
    Simulated publish. Returns a fake platform response on success,
    raises RuntimeError on simulated failure (so Celery's retry/backoff
    kicks in exactly the way it would for a real transient API error).
    """
    # Simulated network latency, so status transitions (Publishing -> ...)
    # are actually observable in the UI instead of resolving instantly.
    await asyncio.sleep(1.5)

    if random.random() < SIMULATE_FAILURE_RATE:
        raise RuntimeError(
            f"Simulated transient failure publishing to {platform} "
            f"(this is fake — real integration goes here)"
        )

    return {
        "platform": platform,
        "external_post_id": f"simulated-{random.randint(100000, 999999)}",
        "published": True,
    }
