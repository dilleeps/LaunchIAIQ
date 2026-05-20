import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { Card } from "../components/ui/card";
import { Select } from "../components/ui/select";

interface PathwaySummary {
  key: string;
  name: string;
  regulator: string;
  typical_total_days: number;
  gate_count: number;
  summary: string;
}

interface Gate {
  key: string;
  name: string;
  duration_d: [number, number, number];
  depends: string[];
  optional?: boolean;
  description?: string;
  artefact?: string;
  failure_mode?: string;
}

interface Pathway {
  key: string;
  name: string;
  regulator: string;
  typical_total_days: number;
  summary: string;
  gates: Gate[];
}

export function Regulatory() {
  const { data: pathways } = useQuery({
    queryKey: ["regulatory-pathways"],
    queryFn: () => api<PathwaySummary[]>("/regulatory/pathways"),
  });
  const [selectedKey, setSelectedKey] = useState<string>("");
  const activeKey = selectedKey || pathways?.[0]?.key || "";

  const { data: pathway } = useQuery({
    queryKey: ["regulatory-pathway", activeKey],
    queryFn: () => api<Pathway>(`/regulatory/pathways/${activeKey}`),
    enabled: !!activeKey,
  });

  // Earliest-start scheduling using typical durations
  const scheduled = useMemo(() => {
    if (!pathway) return [];
    const byKey = new Map(pathway.gates.map((g) => [g.key, g]));
    const start = new Map<string, number>();
    const end = new Map<string, number>();
    for (const g of pathway.gates) {
      const predEnd = g.depends.length
        ? Math.max(...g.depends.map((d) => end.get(d) ?? 0))
        : 0;
      start.set(g.key, predEnd);
      end.set(g.key, predEnd + g.duration_d[1]);
    }
    const totalDays = Math.max(...Array.from(end.values()));
    return pathway.gates.map((g) => ({
      ...g,
      startDay: start.get(g.key)!,
      endDay: end.get(g.key)!,
      startPct: (start.get(g.key)! / totalDays) * 100,
      widthPct: (g.duration_d[1] / totalDays) * 100,
      minPct: ((end.get(g.key)! - g.duration_d[2] + g.duration_d[0]) / totalDays) * 100,
      maxPct: (g.duration_d[2] / totalDays) * 100,
      depPredEnd: g.depends.length ? Math.max(...g.depends.map((d) => end.get(d) ?? 0)) : 0,
    }));
  }, [pathway]);

  const totalDays = scheduled.length ? Math.max(...scheduled.map((s) => s.endDay)) : 0;
  const totalYears = (totalDays / 365).toFixed(1);

  // Compute month/year markers
  const markers = useMemo(() => {
    if (!totalDays) return [];
    const out: { x: number; label: string }[] = [];
    const yearStep = totalDays > 1460 ? 1 : 0.5;
    for (let y = 0; y * 365 <= totalDays; y += yearStep) {
      out.push({ x: (y * 365 / totalDays) * 100, label: y === 0 ? "Start" : `Y${y}` });
    }
    return out;
  }, [totalDays]);

  return (
    <>
      <PageHeader
        eyebrow="Regulatory pathways"
        title="Hard dependencies & industry benchmarks."
        subtitle="Standard regulatory gate sequences with typical timelines, sourced from FDA PDUFA / BsUFA performance goals, EMA centralised procedure clock, and industry benchmarks. Use these as templates when planning a new launch."
      />

      <div className="px-10 py-6 space-y-6">
        {/* Pathway picker */}
        <Card className="p-5">
          <div className="flex items-end gap-4">
            <div className="flex-1">
              <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Pathway</label>
              <Select value={activeKey} onChange={(e) => setSelectedKey(e.target.value)}>
                {pathways?.map((p) => (
                  <option key={p.key} value={p.key}>
                    {p.name}
                  </option>
                ))}
              </Select>
            </div>
            {pathway && (
              <div className="grid grid-cols-4 gap-6 text-right">
                <Stat label="Regulator" value={pathway.regulator} />
                <Stat label="Gates" value={pathway.gates.length} />
                <Stat label="Typical timeline" value={`${totalYears} yr`} />
                <Stat label="Optional gates" value={pathway.gates.filter((g) => g.optional).length} />
              </div>
            )}
          </div>
          {pathway && <p className="text-sm text-mute-2 mt-3">{pathway.summary}</p>}
        </Card>

        {/* Timeline visualization */}
        {pathway && (
          <Card className="p-0 overflow-hidden">
            <div className="p-5 border-b border-line">
              <h2 className="font-display text-xl tracking-tight">Critical-path timeline</h2>
              <p className="text-xs text-mute-2 mt-1">
                Each row is a gate. Bar = typical duration. Dashed extension = max regulatory delay observed.
                Dependencies are drawn as <span className="text-primary">teal arrows</span> from predecessor → successor.
              </p>
            </div>

            <div className="grid" style={{ gridTemplateColumns: "320px 1fr 100px" }}>
              {/* Header axis */}
              <div className="border-b border-line bg-paper-2 px-4 py-2 font-mono text-[10px] uppercase tracking-widest text-mute">
                Gate
              </div>
              <div className="border-b border-line bg-paper-2 relative h-9">
                {markers.map((m, i) => (
                  <div
                    key={i}
                    className="absolute top-0 h-full border-l border-line text-[10px] font-mono uppercase tracking-wider text-mute pl-1 pt-2.5"
                    style={{ left: `${m.x}%` }}
                  >
                    {m.label}
                  </div>
                ))}
              </div>
              <div className="border-b border-line bg-paper-2 px-3 py-2 font-mono text-[10px] uppercase tracking-widest text-mute text-right">
                Typical
              </div>

              {scheduled.map((g, idx) => {
                const cumYear = (g.endDay / 365).toFixed(1);
                return (
                  <div key={g.key} className="contents group">
                    {/* Name + key */}
                    <div className="px-4 py-3 border-b border-line bg-paper hover:bg-paper-2">
                      <div className="flex items-baseline gap-2">
                        <span className="font-mono text-[10px] text-mute uppercase tracking-wider">{idx + 1}.</span>
                        <span className="font-medium">{g.name}</span>
                        {g.optional && <span className="chip rag-Pending text-[9px]">optional</span>}
                      </div>
                      {g.description && (
                        <div className="text-[11px] text-mute-2 mt-1 line-clamp-2">{g.description}</div>
                      )}
                      {g.depends.length > 0 && (
                        <div className="text-[10px] text-mute font-mono mt-1">
                          ↳ depends on {g.depends.join(", ")}
                        </div>
                      )}
                    </div>

                    {/* Bar */}
                    <div className="relative border-b border-line bg-paper hover:bg-paper-2 py-3">
                      {/* Max-delay extension (faded) */}
                      <div
                        className="absolute h-2 rounded-sm opacity-30"
                        style={{
                          top: "50%",
                          transform: "translateY(-50%)",
                          left: `${g.startPct}%`,
                          width: `${(g.duration_d[2] / totalDays) * 100}%`,
                          background: g.optional ? "#9CA3AF" : "#165D59",
                        }}
                        title={`Max delay: ${g.duration_d[2]} days`}
                      />
                      {/* Typical bar */}
                      <div
                        className="absolute h-5 rounded shadow-sm"
                        style={{
                          top: "50%",
                          transform: "translateY(-50%)",
                          left: `${g.startPct}%`,
                          width: `${g.widthPct}%`,
                          background: g.optional ? "#9CA3AF" : "#165D59",
                          opacity: g.optional ? 0.7 : 1,
                        }}
                        title={`Typical: ${g.duration_d[1]} days (min ${g.duration_d[0]}, max ${g.duration_d[2]})`}
                      />
                      {/* Dependency arrow markers — small dot at start */}
                      {g.depends.length > 0 && (
                        <div
                          className="absolute w-2 h-2 rounded-full bg-primary"
                          style={{
                            top: "50%",
                            transform: "translate(-50%, -50%)",
                            left: `${g.startPct}%`,
                          }}
                        />
                      )}
                    </div>

                    {/* Days column */}
                    <div className="px-3 py-3 border-b border-line text-right font-mono text-xs">
                      <div className="text-ink-2">{g.duration_d[1]}d</div>
                      <div className="text-[10px] text-mute">cum Y{cumYear}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        )}

        {/* Dependency table */}
        {pathway && (
          <Card className="p-0 overflow-hidden">
            <div className="p-5 border-b border-line">
              <h2 className="font-display text-xl tracking-tight">Gate-by-gate detail</h2>
              <p className="text-xs text-mute-2 mt-1">Click any gate's predecessor list to see hard dependencies. Failure mode shows what a "no-go" looks like.</p>
            </div>
            <table className="w-full text-sm">
              <thead className="bg-paper-2 border-b border-line text-left">
                <tr>
                  <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">#</th>
                  <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Gate</th>
                  <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Min / Typ / Max (d)</th>
                  <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Hard dependencies</th>
                  <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Evidence artefact</th>
                  <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Failure mode</th>
                </tr>
              </thead>
              <tbody>
                {pathway.gates.map((g, i) => (
                  <tr key={g.key} className="border-b border-line last:border-0 align-top">
                    <td className="p-3 font-mono text-xs text-mute">{i + 1}</td>
                    <td className="p-3">
                      <div className="font-medium">{g.name}</div>
                      <div className="font-mono text-[10px] text-mute">{g.key}</div>
                    </td>
                    <td className="p-3 font-mono text-xs">
                      {g.duration_d[0]} / <b>{g.duration_d[1]}</b> / {g.duration_d[2]}
                    </td>
                    <td className="p-3 text-xs font-mono">
                      {g.depends.length === 0 ? <span className="text-mute">(start)</span> : g.depends.join(", ")}
                    </td>
                    <td className="p-3 text-xs text-mute-2">{g.artefact ?? "—"}</td>
                    <td className="p-3 text-xs text-mute-2">{g.failure_mode ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}

        <p className="text-xs text-mute italic">
          Benchmarks compiled from FDA PDUFA VII performance goals, BsUFA III commitment letter, EMA centralised procedure
          regulation (EC No 726/2004), Tufts CSDD time-to-approval analyses, and Deloitte launch playbooks. Actual
          timelines vary materially by therapy area, sponsor experience, and indication complexity.
        </p>
      </div>
    </>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-widest text-mute">{label}</div>
      <div className="font-display text-xl tracking-tight mt-1">{value}</div>
    </div>
  );
}
