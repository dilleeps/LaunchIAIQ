import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card } from "./ui/card";

interface AuditRow {
  id: string;
  at: string;
  user_email: string;
  entity: string;
  entity_id: string;
  action: string;
  before: Record<string, any> | null;
  after: Record<string, any> | null;
}

const ACTION_COLOR: Record<string, string> = {
  create: "rag-Green",
  update: "rag-Amber",
  delete: "rag-Red",
};

function describe(r: AuditRow): string {
  if (r.action === "create") {
    const name = r.after?.name || r.after?.competitor_name || r.after?.description || "";
    return `${r.entity} created${name ? `: ${String(name).slice(0, 60)}` : ""}`;
  }
  if (r.action === "delete") return `${r.entity} deleted`;
  // update — describe what changed
  const keys = Object.keys(r.after ?? {});
  if (keys.length === 0) return `${r.entity} updated`;
  if (keys.length === 1) {
    const k = keys[0];
    return `${r.entity}.${k}: ${String(r.before?.[k] ?? "—").slice(0, 30)} → ${String(r.after?.[k] ?? "—").slice(0, 30)}`;
  }
  return `${r.entity} updated (${keys.join(", ")})`;
}

function timeAgo(iso: string): string {
  const ms = Date.now() - new Date(iso).getTime();
  const m = Math.floor(ms / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d < 7) return `${d}d ago`;
  return new Date(iso).toLocaleDateString();
}

export function ActivityFeed({ launchId, mode = "launch" }: { launchId?: string; mode?: "launch" | "me" }) {
  const url = mode === "me" ? "/me/feed?days=14" : `/launches/${launchId}/activity?days=30`;
  const { data, isLoading } = useQuery({
    queryKey: ["activity", url],
    queryFn: () => api<AuditRow[]>(url),
    enabled: mode === "me" || !!launchId,
  });

  return (
    <Card className="p-0 overflow-hidden">
      <div className="px-5 py-3 border-b border-line flex items-baseline justify-between">
        <h3 className="font-display text-lg tracking-tight">
          {mode === "me" ? "Your watched launches" : "Recent activity"}
        </h3>
        <span className="text-xs text-mute font-mono">{data?.length ?? 0} updates</span>
      </div>
      <div className="max-h-[360px] overflow-y-auto">
        {isLoading && <div className="p-4 text-sm text-mute">Loading…</div>}
        {data?.length === 0 && <div className="p-4 text-sm text-mute">No recent activity.</div>}
        {data?.map((r) => (
          <div key={r.id} className="px-5 py-2.5 border-b border-line last:border-0 hover:bg-paper-2 flex items-start gap-3">
            <span className={`chip ${ACTION_COLOR[r.action] ?? "rag-Pending"} shrink-0 mt-0.5`}>{r.action}</span>
            <div className="flex-1 min-w-0">
              <div className="text-sm truncate">{describe(r)}</div>
              <div className="text-[11px] text-mute font-mono mt-0.5">
                {r.user_email} · {timeAgo(r.at)}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}


export function WatchToggle({ launchId }: { launchId: string }) {
  const { data: list, refetch } = useQuery({
    queryKey: ["watchlist"],
    queryFn: () => api<{ launch_id: string }[]>("/me/watchlist"),
  });
  const watching = list?.some((w) => w.launch_id === launchId) ?? false;

  async function toggle() {
    if (watching) {
      await api(`/launches/${launchId}/watch`, { method: "DELETE" });
    } else {
      await api(`/launches/${launchId}/watch`, { method: "POST" });
    }
    refetch();
  }

  return (
    <button
      onClick={toggle}
      className={`px-3 py-1.5 text-xs font-mono uppercase tracking-wider rounded border ${
        watching
          ? "bg-primary text-primary-foreground border-primary"
          : "border-line text-mute-2 hover:border-line-dark"
      }`}
    >
      {watching ? "★ Watching" : "☆ Watch"}
    </button>
  );
}
