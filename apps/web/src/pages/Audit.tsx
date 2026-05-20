import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { Card } from "../components/ui/card";
import { Select } from "../components/ui/select";
import { Input } from "../components/ui/input";

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

const ENTITIES = ["", "milestone", "task", "launch", "risk", "prd", "forecast", "dependency", "scenario"];
const ACTIONS = ["", "create", "update", "delete"];

export function Audit() {
  const [entity, setEntity] = useState("");
  const [days, setDays] = useState(30);
  const { data, isLoading } = useQuery({
    queryKey: ["audit", entity, days],
    queryFn: () => {
      const params = new URLSearchParams();
      if (entity) params.set("entity", entity);
      params.set("days", String(days));
      return api<AuditRow[]>(`/audit?${params}`);
    },
  });

  return (
    <>
      <PageHeader
        eyebrow="Compliance"
        title="Audit log."
        subtitle="Every write to milestones, tasks, PRDs, risks, forecasts, dependencies — who changed what, when, with before/after values."
      />
      <div className="px-10 py-6">
        <div className="flex gap-4 mb-4">
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Entity</label>
            <Select value={entity} onChange={(e) => setEntity(e.target.value)}>
              {ENTITIES.map((e) => (
                <option key={e} value={e}>{e || "All"}</option>
              ))}
            </Select>
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Days</label>
            <Input type="number" value={days} min={1} max={365} onChange={(e) => setDays(Number(e.target.value) || 30)} />
          </div>
        </div>

        <Card className="overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead className="bg-paper-2 border-b border-line text-left">
              <tr>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">When</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Who</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Entity</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Action</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Diff</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr><td colSpan={5} className="p-4 text-mute">Loading…</td></tr>
              )}
              {data?.length === 0 && (
                <tr><td colSpan={5} className="p-4 text-mute">No entries match.</td></tr>
              )}
              {data?.map((r) => (
                <tr key={r.id} className="border-b border-line last:border-0 align-top">
                  <td className="p-3 font-mono text-xs whitespace-nowrap">{new Date(r.at).toLocaleString()}</td>
                  <td className="p-3 text-mute-2 text-xs">{r.user_email}</td>
                  <td className="p-3">
                    <div>{r.entity}</div>
                    <div className="font-mono text-[10px] text-mute">{r.entity_id.slice(0, 8)}…</div>
                  </td>
                  <td className="p-3">
                    <span className={`chip ${r.action === "create" ? "rag-Green" : r.action === "delete" ? "rag-Red" : "rag-Amber"}`}>
                      {r.action}
                    </span>
                  </td>
                  <td className="p-3 font-mono text-xs">
                    {r.before && r.after && (
                      <table className="border-collapse">
                        <tbody>
                          {Object.keys(r.after ?? {}).map((k) => (
                            <tr key={k}>
                              <td className="pr-2 text-mute">{k}:</td>
                              <td className="pr-2 line-through text-mute opacity-70">{String(r.before?.[k] ?? "—")}</td>
                              <td className="text-primary">→ {String(r.after?.[k] ?? "—")}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                    {!r.before && r.after && (
                      <span className="text-primary">+ {JSON.stringify(r.after).slice(0, 120)}</span>
                    )}
                    {r.before && !r.after && (
                      <span className="text-destructive">- {JSON.stringify(r.before).slice(0, 120)}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </>
  );
}
