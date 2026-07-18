"""
Request/response schemas for the AI Content Writer service.
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field

Platform = Literal["linkedin", "x"]
Tone = Literal["professional", "casual", "bold", "storytelling"]
Length = Literal["short", "medium", "long"]


class BrandVoice(BaseModel):
    """A saved brand/personal voice profile the AI should write in."""
    id: Optional[str] = None
    user_id: str
    name: str = Field(..., description="Label for this voice profile, e.g. 'Personal - LinkedIn'")
    description: str = Field(..., description="Free-text notes: industry, audience, values, phrases to use/avoid")
    sample_text: Optional[str] = Field(None, description="Optional writing sample to imitate")


class GenerateRequest(BaseModel):
    user_id: str
    platform: Platform
    topic: str = Field(..., description="Topic, idea, or rough notes to turn into a post")
    tone: Tone = "professional"
    length: Length = "medium"
    brand_voice_id: Optional[str] = None
    include_hashtags: bool = True


class GenerateResponse(BaseModel):
    platform: Platform
    draft: str
    hashtags: list[str] = []
    is_thread: bool = False
    thread_parts: Optional[list[str]] = None


class RefineRequest(BaseModel):
    user_id: str
    platform: Platform
    current_draft: str
    instruction: str = Field(..., description="e.g. 'make it shorter', 'add a hook', 'more casual'")
    brand_voice_id: Optional[str] = None


class RefineResponse(BaseModel):
    draft: str


class ArticleRequest(BaseModel):
    user_id: str
    topic: str
    tone: Tone = "professional"
    brand_voice_id: Optional[str] = None
    target_sections: int = Field(4, ge=2, le=8)


class ArticleResponse(BaseModel):
    title: str
    sections: list[dict]  # [{"heading": str, "body": str}]
    conclusion: str
    hashtags: list[str] = []


PostStatus = Literal["scheduled", "publishing", "published", "failed", "cancelled"]


class ScheduleRequest(BaseModel):
    user_id: str
    platform: Platform
    draft: str = Field(..., description="The finished, user-approved draft text to publish")
    scheduled_time: str = Field(..., description="ISO 8601 datetime, e.g. 2026-07-20T09:00:00Z")


class ScheduledPost(BaseModel):
    id: str
    user_id: str
    platform: Platform
    draft: str
    scheduled_time: str
    status: PostStatus
    attempts: int = 0
    last_error: Optional[str] = None


class HashtagRequest(BaseModel):
    platform: Platform
    text: str
    count: int = 5


class HashtagResponse(BaseModel):
    hashtags: list[str]
