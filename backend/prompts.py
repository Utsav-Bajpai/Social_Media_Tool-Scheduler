"""
Prompt templates for each platform / format.

Kept separate from main.py on purpose (per the project spec: "Store prompt
templates so they're easy to tune without code changes"). A non-engineer
could edit the strings below without touching the API code.
"""

TONE_GUIDANCE = {
    "professional": "polished, confident, industry-appropriate language",
    "casual": "conversational, relaxed, like talking to a peer",
    "bold": "punchy, opinionated, unafraid to take a stance",
    "storytelling": "narrative-driven, uses a scene or anecdote to make the point",
}

LENGTH_GUIDANCE = {
    "short": "very brief, 2-3 sentences max",
    "medium": "a solid full post, several short paragraphs",
    "long": "a fuller post that goes deep on the topic while staying skimmable",
}

BRAND_VOICE_BLOCK = """
Brand voice profile to write in:
Name: {name}
Notes: {description}
{sample_block}
""".strip()


def brand_voice_block(voice: dict | None) -> str:
    if not voice:
        return ""
    sample = f"Sample of their writing style:\n{voice['sample_text']}" if voice.get("sample_text") else ""
    return BRAND_VOICE_BLOCK.format(
        name=voice.get("name", ""),
        description=voice.get("description", ""),
        sample_block=sample,
    )


LINKEDIN_POST_PROMPT = """
You are a LinkedIn ghostwriter. Write a ready-to-post LinkedIn update.

Topic / notes from the user: {topic}

Tone: {tone} ({tone_guidance})
Length: {length_guidance}
{brand_voice}

Structure it as: a scroll-stopping hook (first line), a value-driven middle
section (insight, lesson, or story), and a clear call-to-action or
reflective closing line. Use short paragraphs and line breaks the way
LinkedIn posts are actually formatted (no walls of text).
{hashtag_instruction}

Return ONLY the post text, nothing else.
""".strip()

X_POST_PROMPT = """
You are an X (Twitter) ghostwriter. Write a punchy, ready-to-post tweet.

Topic / notes from the user: {topic}

Tone: {tone} ({tone_guidance})
Length: {length_guidance}
{brand_voice}

Hard constraint: stay under 280 characters. Be direct, no fluff, no
hashtag-stuffing.
{hashtag_instruction}

If the topic genuinely needs more than 280 characters to do justice to,
instead write a thread: return each tweet on its own line, prefixed with
"1/", "2/", etc. Otherwise return a single tweet with no prefix.

Return ONLY the tweet(s), nothing else.
""".strip()

REFINE_PROMPT = """
You are editing an existing {platform} post per the user's instruction.

Current draft:
---
{current_draft}
---

Instruction: {instruction}
{brand_voice}

Apply the instruction faithfully. Keep everything else about the post
(claims, structure, voice) the same unless the instruction implies
otherwise. Preserve platform constraints (280 chars for a single X post).

Return ONLY the revised draft, nothing else.
""".strip()

ARTICLE_PROMPT = """
You are writing a full LinkedIn article (long-form, not a short post).

Topic / notes from the user: {topic}
Tone: {tone} ({tone_guidance})
{brand_voice}

Produce:
1. A compelling title
2. {target_sections} sections, each with a short heading and a body of
   2-4 paragraphs
3. A conclusion paragraph that ties it together and invites engagement
4. 3-5 relevant hashtags

Return this as valid JSON with exactly this shape, and nothing else
(no markdown fences, no commentary):
{{
  "title": "...",
  "sections": [{{"heading": "...", "body": "..."}}, ...],
  "conclusion": "...",
  "hashtags": ["...", ...]
}}
""".strip()

HASHTAG_PROMPT = """
Suggest {count} relevant hashtags for this {platform} post. Mix broad and
niche tags. No commentary, return ONLY a JSON array of strings, e.g.
["#Example", "#AnotherTag"].

Post text:
---
{text}
---
""".strip()


def hashtag_instruction(include: bool) -> str:
    if include:
        return "Include 2-4 relevant hashtags worked naturally into or after the post."
    return "Do not include any hashtags."
