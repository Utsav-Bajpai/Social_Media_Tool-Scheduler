"""
Thin wrapper around the Gemini API so the rest of the app never touches
the SDK directly (makes it easy to swap models or add caching/retries
in one place later).
"""
import json
import os

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()  # reads backend/.env so GEMINI_API_KEY is available to os.getenv below

_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_configured = False


def _ensure_configured() -> None:
    global _configured
    if _configured:
        return
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to backend/.env (see .env.example)."
        )
    genai.configure(api_key=api_key)
    _configured = True


async def generate_text(prompt: str, temperature: float = 0.9) -> str:
    """Send a prompt to Gemini and return the raw text response."""
    _ensure_configured()
    model = genai.GenerativeModel(_MODEL_NAME)
    response = await model.generate_content_async(
        prompt,
        generation_config={"temperature": temperature},
    )
    return (response.text or "").strip()


async def generate_json(prompt: str, temperature: float = 0.8) -> dict:
    """Send a prompt that asks for JSON back, and parse it defensively."""
    raw = await generate_text(prompt, temperature=temperature)
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model did not return valid JSON: {raw[:300]}") from exc
