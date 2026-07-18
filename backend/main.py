"""
AI Content Writer service — LinkedIn & X post/article generation.

Covers the "4. AI Content Writing" pillar of the Social Media Management
Tool spec:
  - Post generator (topic -> ready-to-post draft, per-platform style)
  - LinkedIn long-form articles
  - Tone & length controls
  - Brand voice profile (saved + applied on every generation)
  - Regenerate / refine
  - Hashtag suggestions
Drafts are always returned to the caller for editing before posting —
this service never posts anything itself (that's the Auto-Posting module).
"""
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import gemini_client
import prompts
import scheduler_storage
import storage
from celery_app import celery_app
from models import (
    ArticleRequest,
    ArticleResponse,
    BrandVoice,
    GenerateRequest,
    GenerateResponse,
    HashtagRequest,
    HashtagResponse,
    RefineRequest,
    RefineResponse,
    ScheduledPost,
    ScheduleRequest,
)
from scheduler_tasks import publish_post_task

app = FastAPI(title="AI Content Writer", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the Next.js origin before shipping
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------- Brand voice profiles ----------

@app.post("/brand-voice", response_model=BrandVoice)
async def create_brand_voice(voice: BrandVoice):
    saved = storage.save_brand_voice(voice.model_dump())
    return saved


@app.get("/brand-voice/{user_id}", response_model=list[BrandVoice])
async def list_brand_voices(user_id: str):
    return storage.list_brand_voices(user_id)


# ---------- Post generation ----------

@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    voice = storage.get_brand_voice(req.brand_voice_id) if req.brand_voice_id else None

    if req.platform == "linkedin":
        prompt = prompts.LINKEDIN_POST_PROMPT.format(
            topic=req.topic,
            tone=req.tone,
            tone_guidance=prompts.TONE_GUIDANCE[req.tone],
            length_guidance=prompts.LENGTH_GUIDANCE[req.length],
            brand_voice=prompts.brand_voice_block(voice),
            hashtag_instruction=prompts.hashtag_instruction(req.include_hashtags),
        )
        draft = await gemini_client.generate_text(prompt)
        return GenerateResponse(platform="linkedin", draft=draft)

    # platform == "x"
    prompt = prompts.X_POST_PROMPT.format(
        topic=req.topic,
        tone=req.tone,
        tone_guidance=prompts.TONE_GUIDANCE[req.tone],
        length_guidance=prompts.LENGTH_GUIDANCE[req.length],
        brand_voice=prompts.brand_voice_block(voice),
        hashtag_instruction=prompts.hashtag_instruction(req.include_hashtags),
    )
    draft = await gemini_client.generate_text(prompt)

    is_thread = "\n1/" in f"\n{draft}" or draft.strip().startswith("1/")
    if is_thread:
        parts = [line.strip() for line in draft.splitlines() if line.strip()]
        return GenerateResponse(platform="x", draft=draft, is_thread=True, thread_parts=parts)
    return GenerateResponse(platform="x", draft=draft, is_thread=False)


@app.post("/refine", response_model=RefineResponse)
async def refine(req: RefineRequest):
    voice = storage.get_brand_voice(req.brand_voice_id) if req.brand_voice_id else None
    prompt = prompts.REFINE_PROMPT.format(
        platform=req.platform,
        current_draft=req.current_draft,
        instruction=req.instruction,
        brand_voice=prompts.brand_voice_block(voice),
    )
    draft = await gemini_client.generate_text(prompt, temperature=0.7)
    return RefineResponse(draft=draft)


@app.post("/article", response_model=ArticleResponse)
async def generate_article(req: ArticleRequest):
    voice = storage.get_brand_voice(req.brand_voice_id) if req.brand_voice_id else None
    prompt = prompts.ARTICLE_PROMPT.format(
        topic=req.topic,
        tone=req.tone,
        tone_guidance=prompts.TONE_GUIDANCE[req.tone],
        brand_voice=prompts.brand_voice_block(voice),
        target_sections=req.target_sections,
    )
    try:
        data = await gemini_client.generate_json(prompt)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ArticleResponse(
        title=data.get("title", ""),
        sections=data.get("sections", []),
        conclusion=data.get("conclusion", ""),
        hashtags=data.get("hashtags", []),
    )


@app.post("/hashtags", response_model=HashtagResponse)
async def suggest_hashtags(req: HashtagRequest):
    prompt = prompts.HASHTAG_PROMPT.format(
        count=req.count, platform=req.platform, text=req.text
    )
    raw = await gemini_client.generate_text(prompt, temperature=0.6)
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    import json

    try:
        tags = json.loads(cleaned)
    except json.JSONDecodeError:
        # fall back to naive line-splitting if the model didn't return clean JSON
        tags = [t.strip() for t in raw.replace(",", "\n").splitlines() if t.strip().startswith("#")]
    return HashtagResponse(hashtags=tags)


# ---------- Scheduling (Auto-Posting) ----------
# Publishing itself is simulated for now — see publisher.py for the single
# swap point where real platform API calls get added later.

@app.post("/schedule", response_model=ScheduledPost)
async def schedule_post(req: ScheduleRequest):
    try:
        scheduled_dt = datetime.fromisoformat(req.scheduled_time.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="scheduled_time must be ISO 8601, e.g. 2026-07-20T09:00:00Z")

    if scheduled_dt <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="scheduled_time must be in the future")

    post = scheduler_storage.create_scheduled_post(
        {
            "user_id": req.user_id,
            "platform": req.platform,
            "draft": req.draft,
            "scheduled_time": req.scheduled_time,
            "status": "scheduled",
        }
    )

    # Enqueue on Celery with an ETA — the worker won't pick this up until
    # that exact time, even though it's queued immediately.
    task = publish_post_task.apply_async(
        args=[post["id"], req.platform, req.draft, req.user_id],
        eta=scheduled_dt,
    )
    scheduler_storage.update_status(post["id"], status="scheduled")
    post["celery_task_id"] = task.id

    return post


@app.get("/scheduled/{user_id}", response_model=list[ScheduledPost])
async def list_scheduled(user_id: str):
    return scheduler_storage.list_scheduled_posts(user_id)


@app.get("/scheduled/post/{post_id}", response_model=ScheduledPost)
async def get_scheduled(post_id: str):
    post = scheduler_storage.get_scheduled_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")
    return post


@app.delete("/scheduled/post/{post_id}")
async def cancel_scheduled(post_id: str):
    post = scheduler_storage.get_scheduled_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")
    if post.get("celery_task_id"):
        celery_app.control.revoke(post["celery_task_id"])
    scheduler_storage.update_status(post_id, status="cancelled")
    return {"id": post_id, "status": "cancelled"}
