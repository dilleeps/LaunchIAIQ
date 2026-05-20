import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";

interface Comment {
  id: string;
  section: string;
  field: string;
  body: string;
  mentions: string[];
  user_email?: string;
  created_at: string;
  resolved_at?: string | null;
}

export function PRDComments({ prdId }: { prdId: string }) {
  const qc = useQueryClient();
  const { data: comments } = useQuery({
    queryKey: ["prd-comments", prdId],
    queryFn: () => api<Comment[]>(`/prds/${prdId}/comments`),
  });
  const [body, setBody] = useState("");
  const [section, setSection] = useState("executive_summary");
  const [field, setField] = useState("launch_vision");

  const add = useMutation({
    mutationFn: () =>
      api(`/prds/${prdId}/comments`, {
        method: "POST",
        body: JSON.stringify({ section, field, body, mentions: extractMentions(body) }),
      }),
    onSuccess: () => {
      setBody("");
      qc.invalidateQueries({ queryKey: ["prd-comments", prdId] });
    },
  });

  const resolve = useMutation({
    mutationFn: (id: string) => api(`/comments/${id}/resolve`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["prd-comments", prdId] }),
  });

  const unresolved = (comments || []).filter((c) => !c.resolved_at);
  const resolved = (comments || []).filter((c) => c.resolved_at);

  return (
    <Card className="p-0 overflow-hidden sticky top-4">
      <div className="px-4 py-3 border-b border-line">
        <h3 className="font-display text-lg tracking-tight">Comments</h3>
        <p className="text-xs text-mute-2 mt-0.5">@mention with @name to ping</p>
      </div>

      <div className="p-4 border-b border-line space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <Input value={section} onChange={(e) => setSection(e.target.value)} placeholder="section" className="text-xs" />
          <Input value={field} onChange={(e) => setField(e.target.value)} placeholder="field" className="text-xs" />
        </div>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Comment or question (use @mention)…"
          className="w-full text-sm border border-line rounded p-2 min-h-[60px] focus:outline-none focus:border-primary"
        />
        <Button
          size="sm"
          className="w-full"
          disabled={!body.trim() || add.isPending}
          onClick={() => add.mutate()}
        >
          {add.isPending ? "Posting…" : "Post comment"}
        </Button>
      </div>

      <div className="max-h-[440px] overflow-y-auto">
        {unresolved.length === 0 && resolved.length === 0 && (
          <div className="p-4 text-xs text-mute">No comments yet.</div>
        )}
        {unresolved.length > 0 && (
          <div className="px-4 py-2 font-mono text-[10px] uppercase tracking-widest text-mute bg-paper-2">
            Open ({unresolved.length})
          </div>
        )}
        {unresolved.map((c) => (
          <CommentRow key={c.id} c={c} onResolve={() => resolve.mutate(c.id)} />
        ))}
        {resolved.length > 0 && (
          <div className="px-4 py-2 font-mono text-[10px] uppercase tracking-widest text-mute bg-paper-2">
            Resolved ({resolved.length})
          </div>
        )}
        {resolved.map((c) => (
          <CommentRow key={c.id} c={c} muted />
        ))}
      </div>
    </Card>
  );
}

function CommentRow({ c, onResolve, muted }: { c: Comment; onResolve?: () => void; muted?: boolean }) {
  return (
    <div className={`p-4 border-b border-line last:border-0 ${muted ? "opacity-60" : ""}`}>
      <div className="flex items-baseline justify-between mb-1">
        <span className="font-mono text-[10px] uppercase tracking-wider text-mute">
          {c.section} · {c.field}
        </span>
        <span className="font-mono text-[10px] text-mute">{new Date(c.created_at).toLocaleString()}</span>
      </div>
      <div className="text-sm">{highlight(c.body)}</div>
      {c.user_email && <div className="text-[10px] text-mute mt-1">{c.user_email}</div>}
      {onResolve && (
        <button
          onClick={onResolve}
          className="mt-2 text-[10px] font-mono uppercase tracking-wider text-primary hover:underline"
        >
          Resolve
        </button>
      )}
    </div>
  );
}

function highlight(text: string) {
  // Highlight @mentions
  const parts = text.split(/(@[a-zA-Z0-9._-]+)/g);
  return parts.map((p, i) =>
    p.startsWith("@") ? <span key={i} className="text-primary font-medium">{p}</span> : <span key={i}>{p}</span>
  );
}

function extractMentions(text: string): string[] {
  return Array.from(text.matchAll(/@([a-zA-Z0-9._-]+)/g)).map((m) => m[1]);
}
