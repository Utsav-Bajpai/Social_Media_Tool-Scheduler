"""
Persistence for scheduled posts.

Same pattern as storage.py: uses Supabase when SUPABASE_URL / SUPABASE_KEY
are set, falls back to an in-memory store otherwise. Note the in-memory
store here only works correctly when the API process and the Celery
worker are the same process (they're not, in production) — it's fine for
quick local testing but set up Supabase before the demo so status updates
made by the worker are actually visible to the API.

Expected Supabase table:

    create table scheduled_posts (
        id uuid primary key default gen_random_uuid(),
        user_id text not null,
        platform text not null,
        draft text not null,
        scheduled_time timestamptz not null,
        status text not null default 'scheduled',
        attempts int not null default 0,
        last_error text,
        celery_task_id text,
        created_at timestamptz default now(),
        updated_at timestamptz default now()
    );
"""
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

_memory_store: dict[str, dict] = {}

_supabase = None


def _get_client():
    global _supabase
    if _supabase is not None:
        return _supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        return None
    from supabase import create_client

    _supabase = create_client(url, key)
    return _supabase


def create_scheduled_post(post: dict) -> dict:
    post = dict(post)
    post["id"] = post.get("id") or str(uuid.uuid4())
    post.setdefault("status", "scheduled")
    post.setdefault("attempts", 0)
    post["updated_at"] = datetime.now(timezone.utc).isoformat()

    client = _get_client()
    if client is None:
        _memory_store[post["id"]] = post
        return post
    client.table("scheduled_posts").upsert(post).execute()
    return post


def update_status(post_id: str, status: str, attempts: Optional[int] = None, error: Optional[str] = None) -> None:
    updates = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    if attempts is not None:
        updates["attempts"] = attempts
    if error is not None:
        updates["last_error"] = error

    client = _get_client()
    if client is None:
        if post_id in _memory_store:
            _memory_store[post_id].update(updates)
        return
    client.table("scheduled_posts").update(updates).eq("id", post_id).execute()


def get_scheduled_post(post_id: str) -> Optional[dict]:
    client = _get_client()
    if client is None:
        return _memory_store.get(post_id)
    result = client.table("scheduled_posts").select("*").eq("id", post_id).limit(1).execute()
    return result.data[0] if result.data else None


def list_scheduled_posts(user_id: str) -> list[dict]:
    client = _get_client()
    if client is None:
        return sorted(
            [p for p in _memory_store.values() if p["user_id"] == user_id],
            key=lambda p: p["scheduled_time"],
        )
    result = (
        client.table("scheduled_posts")
        .select("*")
        .eq("user_id", user_id)
        .order("scheduled_time")
        .execute()
    )
    return result.data
