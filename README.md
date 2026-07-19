## Stack

- **Frontend:** Next.js 14 (App Router) + Tailwind
- **Backend:** FastAPI
- **AI:** Gemini API
- **Scheduling:** Celery + Redis (Upstash in production)
- **Storage:** Supabase (brand voice profiles, scheduled posts)

## Commands to Run it locally

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

# Windows
celery -A celery_app worker --loglevel=info --pool=solo
```

Leave this running in its own terminal. Without it, scheduled posts will
sit at status `scheduled` forever — nothing ever picks them up.

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```