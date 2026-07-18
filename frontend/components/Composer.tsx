"use client";

import { useEffect, useState } from "react";
import {
  BrandVoice,
  Length,
  Platform,
  Tone,
  generateArticle,
  generatePost,
  listBrandVoices,
  refinePost,
  saveBrandVoice,
  schedulePost,
  suggestHashtags,
} from "@/lib/api";
import ScheduledPosts from "@/components/ScheduledPosts";

const USER_ID = "demo-user"; // swap for the authenticated Supabase user id

const TONES: Tone[] = ["professional", "casual", "bold", "storytelling"];
const LENGTHS: Length[] = ["short", "medium", "long"];

type Mode = "post" | "article";

export default function Composer() {
  const [platform, setPlatform] = useState<Platform>("linkedin");
  const [mode, setMode] = useState<Mode>("post");
  const [topic, setTopic] = useState("");
  const [tone, setTone] = useState<Tone>("professional");
  const [length, setLength] = useState<Length>("medium");
  const [includeHashtags, setIncludeHashtags] = useState(true);

  const [voices, setVoices] = useState<BrandVoice[]>([]);
  const [voiceId, setVoiceId] = useState<string>("");
  const [voiceFormOpen, setVoiceFormOpen] = useState(false);
  const [newVoice, setNewVoice] = useState({ name: "", description: "", sample_text: "" });

  const [draft, setDraft] = useState("");
  const [hashtags, setHashtags] = useState<string[]>([]);
  const [article, setArticle] = useState<{
    title: string;
    sections: { heading: string; body: string }[];
    conclusion: string;
    hashtags: string[];
  } | null>(null);

  const [refineInstruction, setRefineInstruction] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [scheduleTime, setScheduleTime] = useState("");
  const [scheduling, setScheduling] = useState(false);
  const [scheduleMessage, setScheduleMessage] = useState("");

  useEffect(() => {
    listBrandVoices(USER_ID).then(setVoices).catch(() => setVoices([]));
  }, []);

  async function handleGenerate() {
    if (!topic.trim()) return;
    setLoading(true);
    setError("");
    try {
      if (mode === "article") {
        const res = await generateArticle({
          user_id: USER_ID,
          topic,
          tone,
          brand_voice_id: voiceId || undefined,
          target_sections: 4,
        });
        setArticle(res);
        setDraft("");
      } else {
        const res = await generatePost({
          user_id: USER_ID,
          platform,
          topic,
          tone,
          length,
          brand_voice_id: voiceId || undefined,
          include_hashtags: includeHashtags,
        });
        setDraft(res.draft);
        setHashtags(res.hashtags || []);
        setArticle(null);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRefine() {
    if (!refineInstruction.trim() || !draft) return;
    setLoading(true);
    setError("");
    try {
      const res = await refinePost({
        user_id: USER_ID,
        platform,
        current_draft: draft,
        instruction: refineInstruction,
        brand_voice_id: voiceId || undefined,
      });
      setDraft(res.draft);
      setRefineInstruction("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  async function handleHashtags() {
    if (!draft) return;
    try {
      const res = await suggestHashtags({ platform, text: draft, count: 5 });
      setHashtags(res.hashtags);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't fetch hashtags.");
    }
  }

  async function handleSaveVoice() {
    if (!newVoice.name.trim() || !newVoice.description.trim()) return;
    const saved = await saveBrandVoice({ user_id: USER_ID, ...newVoice });
    setVoices((prev) => [...prev, saved]);
    setVoiceId(saved.id || "");
    setVoiceFormOpen(false);
    setNewVoice({ name: "", description: "", sample_text: "" });
  }

  async function handleSchedule() {
    if (!draft || !scheduleTime) return;
    setScheduling(true);
    setScheduleMessage("");
    setError("");
    try {
      // datetime-local gives a value with no timezone; treat it as local time.
      const iso = new Date(scheduleTime).toISOString();
      await schedulePost({ user_id: USER_ID, platform, draft, scheduled_time: iso });
      setScheduleMessage("Scheduled. Publishing is simulated for now — see it below.");
      setScheduleTime("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't schedule this post.");
    } finally {
      setScheduling(false);
    }
  }

  const charCount = draft.length;
  const overLimit = platform === "x" && charCount > 280;

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <header className="mb-10 flex items-baseline justify-between border-b border-rule pb-6">
        <div>
          <h1 className="font-display text-4xl italic text-pineDeep">Draft</h1>
          <p className="mt-1 text-sm text-muted">
            Give it an idea. It hands back something worth posting.
          </p>
        </div>
        <span className="font-mono text-xs uppercase tracking-wider text-muted">
          AI Content Writer · LinkedIn &amp; X
        </span>
      </header>

      <div className="grid grid-cols-1 gap-10 md:grid-cols-2">
        {/* ---- Left: inputs ---- */}
        <section className="space-y-6">
          <div className="flex gap-2">
            {(["linkedin", "x"] as Platform[]).map((p) => (
              <button
                key={p}
                onClick={() => setPlatform(p)}
                className={`rounded-full border px-4 py-1.5 font-mono text-xs uppercase tracking-wide transition-colors ${
                  platform === p
                    ? "border-pine bg-pine text-paper"
                    : "border-rule text-muted hover:border-pine"
                }`}
              >
                {p === "linkedin" ? "LinkedIn" : "X"}
              </button>
            ))}
            {platform === "linkedin" && (
              <div className="ml-auto flex gap-1 rounded-full border border-rule p-1">
                {(["post", "article"] as Mode[]).map((m) => (
                  <button
                    key={m}
                    onClick={() => setMode(m)}
                    className={`rounded-full px-3 py-1 font-mono text-xs uppercase tracking-wide transition-colors ${
                      mode === m ? "bg-ink text-paper" : "text-muted"
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div>
            <label className="mb-1 block font-mono text-xs uppercase tracking-wider text-muted">
              Topic or rough notes
            </label>
            <textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              rows={5}
              placeholder="What do you want to write about? Paste rough notes, a link summary, or just a sentence."
              className="w-full resize-none rounded-md border border-rule bg-white/60 p-3 font-body text-sm text-ink placeholder:text-muted/70 focus:border-pine"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block font-mono text-xs uppercase tracking-wider text-muted">
                Tone
              </label>
              <select
                value={tone}
                onChange={(e) => setTone(e.target.value as Tone)}
                className="w-full rounded-md border border-rule bg-white/60 p-2 text-sm capitalize"
              >
                {TONES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            {mode === "post" && (
              <div>
                <label className="mb-1 block font-mono text-xs uppercase tracking-wider text-muted">
                  Length
                </label>
                <select
                  value={length}
                  onChange={(e) => setLength(e.target.value as Length)}
                  className="w-full rounded-md border border-rule bg-white/60 p-2 text-sm capitalize"
                >
                  {LENGTHS.map((l) => (
                    <option key={l} value={l}>
                      {l}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div>
            <div className="mb-1 flex items-center justify-between">
              <label className="font-mono text-xs uppercase tracking-wider text-muted">
                Brand voice
              </label>
              <button
                onClick={() => setVoiceFormOpen((v) => !v)}
                className="font-mono text-xs text-pine underline underline-offset-2"
              >
                {voiceFormOpen ? "cancel" : "+ new voice"}
              </button>
            </div>
            <select
              value={voiceId}
              onChange={(e) => setVoiceId(e.target.value)}
              className="w-full rounded-md border border-rule bg-white/60 p-2 text-sm"
            >
              <option value="">No brand voice — use default tone</option>
              {voices.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name}
                </option>
              ))}
            </select>

            {voiceFormOpen && (
              <div className="mt-3 space-y-2 rounded-md border border-dashed border-rule p-3">
                <input
                  placeholder="Voice name, e.g. 'Founder voice'"
                  value={newVoice.name}
                  onChange={(e) => setNewVoice({ ...newVoice, name: e.target.value })}
                  className="w-full rounded border border-rule bg-white p-2 text-sm"
                />
                <textarea
                  placeholder="Describe the voice: industry, audience, values, phrases to use or avoid"
                  value={newVoice.description}
                  onChange={(e) => setNewVoice({ ...newVoice, description: e.target.value })}
                  rows={2}
                  className="w-full resize-none rounded border border-rule bg-white p-2 text-sm"
                />
                <textarea
                  placeholder="Optional: paste a writing sample to imitate"
                  value={newVoice.sample_text}
                  onChange={(e) => setNewVoice({ ...newVoice, sample_text: e.target.value })}
                  rows={2}
                  className="w-full resize-none rounded border border-rule bg-white p-2 text-sm"
                />
                <button
                  onClick={handleSaveVoice}
                  className="rounded-md bg-pine px-3 py-1.5 font-mono text-xs uppercase tracking-wide text-paper"
                >
                  Save voice
                </button>
              </div>
            )}
          </div>

          {mode === "post" && (
            <label className="flex items-center gap-2 font-mono text-xs uppercase tracking-wider text-muted">
              <input
                type="checkbox"
                checked={includeHashtags}
                onChange={(e) => setIncludeHashtags(e.target.checked)}
              />
              Include hashtags
            </label>
          )}

          <button
            onClick={handleGenerate}
            disabled={loading || !topic.trim()}
            className="w-full rounded-md bg-ink py-3 font-mono text-sm uppercase tracking-wider text-paper transition-opacity disabled:opacity-40"
          >
            {loading ? "Writing…" : mode === "article" ? "Generate article" : "Generate draft"}
          </button>

          {error && <p className="font-mono text-xs text-clay">{error}</p>}
        </section>

        {/* ---- Right: output ---- */}
        <section className="rounded-lg border border-rule bg-white/50 p-6">
          {!draft && !article && (
            <p className="font-mono text-xs uppercase tracking-wider text-muted">
              Your draft will appear here — always editable before anything gets posted.
            </p>
          )}

          {mode === "post" && draft && (
            <div className="space-y-4">
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                rows={10}
                className="w-full resize-none rounded-md border border-rule bg-white p-3 font-body text-sm leading-relaxed focus:border-pine"
              />

              {platform === "x" && (
                <div>
                  <div className="flex h-2 w-full overflow-hidden rounded-full bg-rule/60">
                    <div
                      className={`h-full transition-all ${overLimit ? "bg-clay" : "bg-pine"}`}
                      style={{ width: `${Math.min((charCount / 280) * 100, 100)}%` }}
                    />
                  </div>
                  <p
                    className={`mt-1 font-mono text-xs ${
                      overLimit ? "text-clay" : "text-muted"
                    }`}
                  >
                    {charCount} / 280
                  </p>
                </div>
              )}

              {hashtags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {hashtags.map((h) => (
                    <span
                      key={h}
                      className="rounded-full bg-pine/10 px-3 py-1 font-mono text-xs text-pineDeep"
                    >
                      {h}
                    </span>
                  ))}
                </div>
              )}

              <button
                onClick={handleHashtags}
                className="font-mono text-xs text-pine underline underline-offset-2"
              >
                Suggest hashtags
              </button>

              <div className="border-t border-rule pt-4">
                <label className="mb-1 block font-mono text-xs uppercase tracking-wider text-muted">
                  Refine — e.g. &ldquo;make it shorter&rdquo;, &ldquo;add a hook&rdquo;, &ldquo;more casual&rdquo;
                </label>
                <div className="flex gap-2">
                  <input
                    value={refineInstruction}
                    onChange={(e) => setRefineInstruction(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleRefine()}
                    className="flex-1 rounded-md border border-rule bg-white p-2 text-sm"
                    placeholder="Type an instruction…"
                  />
                  <button
                    onClick={handleRefine}
                    disabled={loading || !refineInstruction.trim()}
                    className="rounded-md border border-ink px-4 font-mono text-xs uppercase tracking-wide disabled:opacity-40"
                  >
                    Apply
                  </button>
                </div>
              </div>

              <div className="border-t border-rule pt-4">
                <label className="mb-1 block font-mono text-xs uppercase tracking-wider text-muted">
                  Schedule this draft
                </label>
                <div className="flex gap-2">
                  <input
                    type="datetime-local"
                    value={scheduleTime}
                    onChange={(e) => setScheduleTime(e.target.value)}
                    className="flex-1 rounded-md border border-rule bg-white p-2 text-sm"
                  />
                  <button
                    onClick={handleSchedule}
                    disabled={scheduling || !scheduleTime || overLimit}
                    className="rounded-md bg-pine px-4 font-mono text-xs uppercase tracking-wide text-paper disabled:opacity-40"
                  >
                    {scheduling ? "Scheduling…" : "Schedule"}
                  </button>
                </div>
                <p className="mt-1 font-mono text-xs text-muted">
                  Publishing is simulated for now — no real posts go out yet.
                </p>
                {scheduleMessage && (
                  <p className="mt-1 font-mono text-xs text-pineDeep">{scheduleMessage}</p>
                )}
              </div>
            </div>
          )}

          {mode === "article" && article && (
            <div className="space-y-4">
              <h2 className="font-display text-2xl italic text-pineDeep">{article.title}</h2>
              {article.sections.map((s, i) => (
                <div key={i}>
                  <h3 className="font-mono text-xs uppercase tracking-wider text-muted">
                    {s.heading}
                  </h3>
                  <p className="mt-1 whitespace-pre-line text-sm leading-relaxed">{s.body}</p>
                </div>
              ))}
              <div>
                <h3 className="font-mono text-xs uppercase tracking-wider text-muted">
                  Conclusion
                </h3>
                <p className="mt-1 text-sm leading-relaxed">{article.conclusion}</p>
              </div>
              {article.hashtags.length > 0 && (
                <div className="flex flex-wrap gap-2 border-t border-rule pt-4">
                  {article.hashtags.map((h) => (
                    <span
                      key={h}
                      className="rounded-full bg-pine/10 px-3 py-1 font-mono text-xs text-pineDeep"
                    >
                      {h}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </section>
      </div>

      <ScheduledPosts userId={USER_ID} />
    </div>
  );
}
