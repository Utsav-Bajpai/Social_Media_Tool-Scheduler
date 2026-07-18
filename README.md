# AI Content Writer + Scheduler

The AI-writing pillar of the Social Media Management Tool, built to spec:
post generation for LinkedIn & X, LinkedIn long-form articles, tone/length
control, saved brand voice, regenerate/refine, and hashtag suggestions —
plus a scheduling layer (job queue, retry-with-backoff, status tracking)
covering the core of the Auto-Posting pillar too. Every draft is shown
for editing before it's ever scheduled.

**Publishing itself is simulated for now** — no real X/LinkedIn/Meta API
calls happen yet. `publisher.py` is the single, clearly-marked place to
drop in real platform calls later; nothing else (queueing, retries,
status tracking, UI) needs to change when that happens.

## Stack

- **Frontend:** Next.js 14 (App Router) + Tailwind
- **Backend:** FastAPI
- **AI:** Gemini API
- **Scheduling:** Celery + Redis (Upstash in production)
- **Storage:** Supabase (brand voice profiles, scheduled posts) — falls
  back to in-memory if no Supabase credentials are set, so it still runs
  standalone

## Run it locally

### Backend

```bash
cd backend
python -m venv venv 
venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env   # then add your GEMINI_API_KEY
uvicorn main:app --reload --port 8000
```

You'll also need a Redis instance for scheduling — for local dev, either
install Redis locally or point `REDIS_URL` at a free Upstash database
(Upstash gives you a `rediss://...` URL — paste it straight in).

### Celery worker

This is a **separate process** from the API — `uvicorn` only enqueues
jobs, this worker is what actually runs them at their scheduled time.
Run it alongside the API (same `backend/` folder, same venv):

```bash
# Mac/Linux
celery -A celery_app worker --loglevel=info

# Windows (Celery's default worker pool doesn't support Windows)
celery -A celery_app worker --loglevel=info --pool=solo
```

Leave this running in its own terminal. Without it, scheduled posts will
sit at status `scheduled` forever — nothing ever picks them up.

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # points at http://localhost:8000 by default
npm run dev
```

Open http://localhost:3000 — pick a platform, describe a topic, generate,
refine, schedule it, and watch it move through the status list at the
bottom of the page (polls every 5s). For LinkedIn, switch to Article mode
for long-form.

**So you can see it end-to-end:** three terminals — `uvicorn` (API),
`celery -A celery_app worker ...` (scheduler), `npm run dev` (frontend).

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/generate` | Topic → ready-to-post LinkedIn or X draft |
| POST | `/refine` | Apply a natural-language edit instruction to a draft |
| POST | `/article` | Topic → full LinkedIn article (title, sections, conclusion, hashtags) |
| POST | `/hashtags` | Suggest hashtags for a given draft |
| POST | `/brand-voice` | Save a brand voice profile |
| GET | `/brand-voice/{user_id}` | List a user's saved voice profiles |
| POST | `/schedule` | Queue a draft to publish at a given time |
| GET | `/scheduled/{user_id}` | List a user's scheduled posts + status |
| GET | `/scheduled/post/{id}` | Get one scheduled post's status |
| DELETE | `/scheduled/post/{id}` | Cancel a pending scheduled post |

## Wiring into the rest of the project

- **Composer UI (Content Calendar module):** the generated draft is plain
  text — hand it straight to that team's post composer, no extra glue
  needed.
- **Auto-Posting module:** the scheduler here covers queueing, retry, and
  status tracking already — the Platform Connections team's real OAuth
  tokens just need to get passed into `publisher.py` when that's ready.
- **Supabase:** set `SUPABASE_URL` / `SUPABASE_KEY` in `backend/.env` once
  the shared project schema exists, and create the `brand_voices` and
  `scheduled_posts` tables (SQL in each storage module's docstring).

## Prompt tuning

All prompt templates live in `backend/prompts.py`, separate from the
route logic, so tone/structure can be tuned without touching the API code.

## Notes on Gemini

Set `GEMINI_MODEL` in `.env` to pin a specific model version; defaults to
`gemini-2.0-flash`. Verify the exact model name against Google's current
docs before the demo — model names get renamed/deprecated over time.
