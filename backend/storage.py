"""
Persistence for brand voice profiles.

Uses Supabase (Postgres) when SUPABASE_URL / SUPABASE_KEY are set. Falls
back to an in-memory store otherwise, so the service still runs for local
dev / demo without live credentials. Swap nothing else in the app when you
add real credentials — same interface either way.

Expected Supabase table (create via SQL editor or a migration):

    create table brand_voices (
        id uuid primary key default gen_random_uuid(),
        user_id text not null,
        name text not null,
        description text not null,
        sample_text text,
        created_at timestamptz default now()
    );
"""
import os
import uuid
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
    from supabase import create_client  # imported lazily so it's optional

    _supabase = create_client(url, key)
    return _supabase


def save_brand_voice(voice: dict) -> dict:
    voice = dict(voice)
    voice["id"] = voice.get("id") or str(uuid.uuid4())
    client = _get_client()
    if client is None:
        _memory_store[voice["id"]] = voice
        return voice
    client.table("brand_voices").upsert(voice).execute()
    return voice


def get_brand_voice(voice_id: str) -> Optional[dict]:
    client = _get_client()
    if client is None:
        return _memory_store.get(voice_id)
    result = client.table("brand_voices").select("*").eq("id", voice_id).limit(1).execute()
    return result.data[0] if result.data else None


def list_brand_voices(user_id: str) -> list[dict]:
    client = _get_client()
    if client is None:
        return [v for v in _memory_store.values() if v["user_id"] == user_id]
    result = client.table("brand_voices").select("*").eq("user_id", user_id).execute()
    return result.data
