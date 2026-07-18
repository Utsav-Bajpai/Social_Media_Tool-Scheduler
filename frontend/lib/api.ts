const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Platform = "linkedin" | "x";
export type Tone = "professional" | "casual" | "bold" | "storytelling";
export type Length = "short" | "medium" | "long";

export interface BrandVoice {
  id?: string;
  user_id: string;
  name: string;
  description: string;
  sample_text?: string;
}

export interface GenerateResponse {
  platform: Platform;
  draft: string;
  hashtags: string[];
  is_thread: boolean;
  thread_parts?: string[];
}

async function request<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json();
}

export function generatePost(input: {
  user_id: string;
  platform: Platform;
  topic: string;
  tone: Tone;
  length: Length;
  brand_voice_id?: string;
  include_hashtags: boolean;
}) {
  return request<GenerateResponse>("/generate", input);
}

export function refinePost(input: {
  user_id: string;
  platform: Platform;
  current_draft: string;
  instruction: string;
  brand_voice_id?: string;
}) {
  return request<{ draft: string }>("/refine", input);
}

export function generateArticle(input: {
  user_id: string;
  topic: string;
  tone: Tone;
  brand_voice_id?: string;
  target_sections: number;
}) {
  return request<{
    title: string;
    sections: { heading: string; body: string }[];
    conclusion: string;
    hashtags: string[];
  }>("/article", input);
}

export function suggestHashtags(input: { platform: Platform; text: string; count: number }) {
  return request<{ hashtags: string[] }>("/hashtags", input);
}

export async function saveBrandVoice(voice: BrandVoice): Promise<BrandVoice> {
  const res = await fetch(`${BASE_URL}/brand-voice`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(voice),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listBrandVoices(userId: string): Promise<BrandVoice[]> {
  const res = await fetch(`${BASE_URL}/brand-voice/${userId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export type PostStatus = "scheduled" | "publishing" | "published" | "failed" | "cancelled";

export interface ScheduledPost {
  id: string;
  user_id: string;
  platform: Platform;
  draft: string;
  scheduled_time: string;
  status: PostStatus;
  attempts: number;
  last_error?: string | null;
}

export function schedulePost(input: {
  user_id: string;
  platform: Platform;
  draft: string;
  scheduled_time: string; // ISO 8601
}): Promise<ScheduledPost> {
  return request<ScheduledPost>("/schedule", input);
}

export async function listScheduledPosts(userId: string): Promise<ScheduledPost[]> {
  const res = await fetch(`${BASE_URL}/scheduled/${userId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function cancelScheduledPost(postId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/scheduled/post/${postId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
}
