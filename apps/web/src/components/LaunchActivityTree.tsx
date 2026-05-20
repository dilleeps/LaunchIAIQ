import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Select } from "./ui/select";
import { Input } from "./ui/input";

interface Activity {
  id: string;
  launch_id: string;
  parent_id: string | null;
  group_key: string;
  group_name: string;
  ordinal: string;
  level: number;
  name: string;
  status: string;
  country_code?: string | null;
  importance: string;
  manual_complete: boolean;
  start_date?: string | null;
  end_date?: string | null;
  organisation?: string | null;
  assigned_count: number;
}

interface SetupResp {
  template_key?: string;
  commercial_launch_date?: string | null;
  regulatory_submission?: string | null;
  regulatory_approval?: string | null;
  pricing_submission?: string | null;
  pricing_approval?: string | null;
  reimbursement_submission?: string | null;
  reimbursement_approval?: string | null;
  trade_stock_available?: string | null;
  brand?: string | null;
  indication_label?: string | null;
}

const STATUS_OPTIONS = ["Not Started", "In Progress", "Complete", "At Risk", "Blocked", "On Hold"];
const STATUS_COLORS: Record<string, string> = {
  "Complete": "bg-[#EDF5EF] text-[#2F7D4F]",
  "In Progress": "bg-primary-soft text-primary",
  "At Risk": "bg-[#FAF1E0] text-[#B8740A]",
  "Blocked": "bg-[#FCEDED] text-destructive",
  "On Hold": "bg-paper-2 text-mute-2",
  "Not Started": "bg-paper-3 text-ink-2",
};

export function LaunchActivityTree({ launchId, brand, indication }: { launchId: string; brand?: string; indication?: string }) {
  const qc = useQueryClient();
  const { data: activities } = useQuery({
    queryKey: ["activities", launchId],
    queryFn: () => api<Activity[]>(`/launches/${launchId}/activities`),
  });
  const { data: setup } = useQuery({
    queryKey: ["setup", launchId],
    queryFn: () => api<SetupResp | null>(`/launches/${launchId}/setup`),
  });
  const [search, setSearch] = useState("");
  const [groupFilter, setGroupFilter] = useState("");
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  const update = useMutation({
    mutationFn: (vars: { id: string; patch: Partial<Activity> }) =>
      api(`/activities/${vars.id}`, { method: "PATCH", body: JSON.stringify(vars.patch) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["activities", launchId] }),
  });

  const groups = useMemo(() => {
    const seen = new Set<string>();
    return (activities || []).filter((a) => {
      if (seen.has(a.group_key)) return false;
      seen.add(a.group_key);
      return true;
    }).map((a) => ({ key: a.group_key, name: a.group_name }));
  }, [activities]);

  const visible = (activities || []).filter((a) => {
    if (groupFilter && a.group_key !== groupFilter) return false;
    if (search && !a.name.toLowerCase().includes(search.toLowerCase())) return false;
    // hide rows whose ancestor is collapsed
    let cur = a;
    let parent = (activities || []).find((p) => p.id === cur.parent_id);
    while (parent) {
      if (collapsed.has(parent.id)) return false;
      cur = parent;
      parent = (activities || []).find((p) => p.id === cur.parent_id);
    }
    return true;
  });

  const completeCount = (activities || []).filter((a) => a.status === "Complete").length;
  const totalCount = (activities || []).length;
  const completePct = totalCount > 0 ? Math.round((completeCount / totalCount) * 100) : 0;

  const monthsToLaunch = setup?.commercial_launch_date
    ? Math.max(0, Math.round((new Date(setup.commercial_launch_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24 * 30)))
    : null;

  return (
    <div className="space-y-4">
      {/* Header banner — mirrors Takeda "Global TAK-279 Plaque Psoriasis" header */}
      <div className="bg-card border border-line rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="font-display text-2xl tracking-tight">
              {brand} {indication ? `· ${indication}` : ""}
            </div>
            <div className="text-xs text-mute-2 font-mono uppercase tracking-wider mt-1">
              {setup?.template_key?.replace(/_/g, " ").toUpperCase() || "—"}
            </div>
          </div>
          <div className="flex items-center gap-6">
            <Pill label="Overall Status" value="Green" valueClass="text-[#2F7D4F]" />
            <Pill
              label="Commercial Launch Date"
              value={setup?.commercial_launch_date ? fmtDate(setup.commercial_launch_date) : "—"}
              note={monthsToLaunch !== null ? `${monthsToLaunch} months` : ""}
            />
            <Pill label={`Activities Complete`} value={`${completeCount} / ${totalCount}`} note={`${completePct}%`} />
          </div>
        </div>

        {/* Key Launch Assumptions banner */}
        <div className="grid grid-cols-7 gap-3 pt-4 border-t border-line">
          <KLAItem label="Regulatory Submission" date={setup?.regulatory_submission} />
          <KLAItem label="Regulatory Approval" date={setup?.regulatory_approval} />
          <KLAItem label="Pricing Submission" date={setup?.pricing_submission} />
          <KLAItem label="Pricing Approval" date={setup?.pricing_approval} />
          <KLAItem label="Reimbursement Submission" date={setup?.reimbursement_submission} />
          <KLAItem label="Reimbursement Approval" date={setup?.reimbursement_approval} />
          <KLAItem label="Trade Stock Available" date={setup?.trade_stock_available} />
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-2">
        <Select value={groupFilter} onChange={(e) => setGroupFilter(e.target.value)} className="w-64">
          <option value="">All groups</option>
          {groups.map((g) => <option key={g.key} value={g.key}>{g.name}</option>)}
        </Select>
        <Input placeholder="Search activities…" value={search} onChange={(e) => setSearch(e.target.value)} className="flex-1" />
        <button
          onClick={() => {
            // expand all
            setCollapsed(new Set());
          }}
          className="text-xs px-3 py-2 border border-line rounded hover:bg-paper-2 font-mono uppercase tracking-wider"
        >
          Expand all
        </button>
        <button
          onClick={() => {
            const allWithChildren = new Set<string>();
            (activities || []).forEach((a) => {
              if ((activities || []).some((c) => c.parent_id === a.id) && a.level >= 2) {
                allWithChildren.add(a.id);
              }
            });
            setCollapsed(allWithChildren);
          }}
          className="text-xs px-3 py-2 border border-line rounded hover:bg-paper-2 font-mono uppercase tracking-wider"
        >
          Collapse L2+
        </button>
      </div>

      {/* Activity tree table */}
      <div className="border border-line rounded-lg overflow-hidden bg-paper">
        <table className="w-full text-sm">
          <thead className="bg-paper-2 border-b border-line">
            <tr className="text-left">
              <th className="p-3 font-mono text-[10px] uppercase tracking-widest text-mute w-20">ID</th>
              <th className="p-3 font-mono text-[10px] uppercase tracking-widest text-mute">Activity</th>
              <th className="p-3 font-mono text-[10px] uppercase tracking-widest text-mute w-32">Status</th>
              <th className="p-3 font-mono text-[10px] uppercase tracking-widest text-mute w-24">Country</th>
              <th className="p-3 font-mono text-[10px] uppercase tracking-widest text-mute w-24">Importance</th>
              <th className="p-3 font-mono text-[10px] uppercase tracking-widest text-mute w-32">Start</th>
              <th className="p-3 font-mono text-[10px] uppercase tracking-widest text-mute w-32">End</th>
              <th className="p-3 font-mono text-[10px] uppercase tracking-widest text-mute w-28">Organisation</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((a) => {
              const hasChildren = (activities || []).some((c) => c.parent_id === a.id);
              const isCollapsed = collapsed.has(a.id);
              const indent = (a.level - 1) * 16;
              return (
                <tr key={a.id} className={`border-b border-line last:border-0 ${a.level === 1 ? "bg-primary-soft/30 font-medium" : ""}`}>
                  <td className="p-3 font-mono text-xs text-mute">{a.ordinal}</td>
                  <td className="p-3" style={{ paddingLeft: 12 + indent }}>
                    {hasChildren && (
                      <button
                        onClick={() => setCollapsed((prev) => {
                          const next = new Set(prev);
                          isCollapsed ? next.delete(a.id) : next.add(a.id);
                          return next;
                        })}
                        className="text-mute mr-1 w-4 inline-block"
                      >
                        {isCollapsed ? "▸" : "▾"}
                      </button>
                    )}
                    {!hasChildren && <span className="w-4 mr-1 inline-block text-mute">·</span>}
                    {a.name}
                  </td>
                  <td className="p-3">
                    <select
                      value={a.status}
                      onChange={(e) => update.mutate({ id: a.id, patch: { status: e.target.value } })}
                      className={`text-xs font-mono uppercase tracking-wider px-2 py-1 rounded ${STATUS_COLORS[a.status] || ""} border-0 focus:outline-none cursor-pointer`}
                    >
                      {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </td>
                  <td className="p-3 text-xs text-mute-2">{a.country_code || "—"}</td>
                  <td className="p-3 text-xs">
                    <span className={a.importance === "Critical" ? "text-destructive font-medium" : a.importance === "High" ? "text-[#B8740A]" : "text-mute-2"}>
                      {a.importance}
                    </span>
                  </td>
                  <td className="p-3 text-xs text-mute-2">
                    <input
                      type="date"
                      value={a.start_date || ""}
                      onChange={(e) => update.mutate({ id: a.id, patch: { start_date: e.target.value || undefined as any } })}
                      className="bg-transparent border-0 text-xs w-full focus:outline-none focus:bg-paper-2 px-1 py-0.5 rounded"
                    />
                  </td>
                  <td className="p-3 text-xs text-mute-2">
                    <input
                      type="date"
                      value={a.end_date || ""}
                      onChange={(e) => update.mutate({ id: a.id, patch: { end_date: e.target.value || undefined as any } })}
                      className="bg-transparent border-0 text-xs w-full focus:outline-none focus:bg-paper-2 px-1 py-0.5 rounded"
                    />
                  </td>
                  <td className="p-3 text-xs text-mute-2">{a.organisation || "—"}</td>
                </tr>
              );
            })}
            {visible.length === 0 && (
              <tr><td colSpan={8} className="p-8 text-center text-mute">No activities match the current filters.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Pill({ label, value, note, valueClass }: { label: string; value: string; note?: string; valueClass?: string }) {
  return (
    <div className="text-right">
      <div className="font-mono text-[10px] uppercase tracking-widest text-mute">{label}</div>
      <div className={`font-display text-xl tracking-tight ${valueClass || ""}`}>{value}</div>
      {note && <div className="text-[10px] text-mute-2 font-mono uppercase tracking-wider">{note}</div>}
    </div>
  );
}

function KLAItem({ label, date }: { label: string; date?: string | null }) {
  return (
    <div className="text-xs">
      <div className="font-mono text-[10px] uppercase tracking-widest text-mute mb-1">{label}</div>
      <div className={date ? "" : "text-mute"}>{date ? fmtDate(date) : "—"}</div>
    </div>
  );
}

function fmtDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { day: "numeric", month: "short", year: "2-digit" });
}
