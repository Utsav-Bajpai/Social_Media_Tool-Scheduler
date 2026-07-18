"use client";

import { useEffect, useState } from "react";
import { PostStatus, ScheduledPost, cancelScheduledPost, listScheduledPosts } from "@/lib/api";

const STATUS_STYLES: Record<PostStatus, string> = {
  scheduled: "bg-pine/10 text-pineDeep",
  publishing: "bg-amber-100 text-amber-800",
  published: "bg-pine text-paper",
  failed: "bg-clay/15 text-clay",
  cancelled: "bg-rule/60 text-muted",
};

export default function ScheduledPosts({ userId }: { userId: string }) {
  const [posts, setPosts] = useState<ScheduledPost[]>([]);
  const [error, setError] = useState("");

  async function refresh() {
    try {
      const data = await listScheduledPosts(userId);
      setPosts(data);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't load scheduled posts.");
    }
  }

  useEffect(() => {
    refresh();
    // Poll every 5s so status changes (Scheduled -> Publishing -> Published)
    // show up without a manual refresh — useful while the worker is running.
    const id = setInterval(refresh, 5000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  async function handleCancel(id: string) {
    await cancelScheduledPost(id);
    refresh();
  }

  if (posts.length === 0 && !error) return null;

  return (
    <section className="mx-auto mt-10 max-w-5xl px-6">
      <h2 className="mb-3 font-mono text-xs uppercase tracking-wider text-muted">
        Scheduled posts
      </h2>
      {error && <p className="mb-2 font-mono text-xs text-clay">{error}</p>}
      <div className="space-y-2">
        {posts.map((p) => (
          <div
            key={p.id}
            className="flex items-center justify-between gap-4 rounded-md border border-rule bg-white/50 p-3"
          >
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm">{p.draft}</p>
              <p className="mt-0.5 font-mono text-xs text-muted">
                {p.platform === "linkedin" ? "LinkedIn" : "X"} ·{" "}
                {new Date(p.scheduled_time).toLocaleString()}
                {p.attempts > 0 && ` · attempt ${p.attempts}`}
              </p>
              {p.status === "failed" && p.last_error && (
                <p className="mt-0.5 font-mono text-xs text-clay">{p.last_error}</p>
              )}
            </div>
            <span
              className={`shrink-0 rounded-full px-3 py-1 font-mono text-xs uppercase tracking-wide ${STATUS_STYLES[p.status]}`}
            >
              {p.status}
            </span>
            {(p.status === "scheduled" || p.status === "publishing") && (
              <button
                onClick={() => handleCancel(p.id)}
                className="shrink-0 font-mono text-xs text-muted underline underline-offset-2 hover:text-clay"
              >
                Cancel
              </button>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
