import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { Card } from "../components/ui/card";

interface Row {
  launch_id: string;
  launch_code: string;
  asset: string;
  country: string;
  target_launch_date: string | null;
  overall_rag: string;
  composite_score: number;
  band: "Ready" | "Tracking" | "At risk" | "Behind";
  workstreams: Record<string, number | null>;
  high_risks: number;
}

const BAND_STYLE: Record<string, string> = {
  "Ready":    "bg-[#EDF5EF] text-[#2F7D4F]",
  "Tracking": "bg-[#FAF1E0] text-[#B8740A]",
  "At risk":  "bg-[#FBE8EB] text-[#C8102E]",
  "Behind":   "bg-[#FBE8EB] text-[#C8102E]",
};

export function Readiness() {
  const { data } = useQuery({
    queryKey: ["portfolio-readiness"],
    queryFn: () => api<Row[]>("/portfolio/readiness"),
  });

  const summary = (data || []).reduce(
    (acc, r) => {
      acc[r.band] = (acc[r.band] || 0) + 1;
      acc.avg += r.composite_score;
      acc.count++;
      return acc;
    },
    { Ready: 0, Tracking: 0, "At risk": 0, Behind: 0, avg: 0, count: 0 } as any
  );
  const avg = summary.count ? (summary.avg / summary.count).toFixed(1) : "—";

  const workstreams = ["Regulatory", "Market Access", "Commercial", "Medical", "Supply Chain", "Compliance"];

  return (
    <>
      <PageHeader
        eyebrow="Launch readiness"
        title="Are we ready?"
        subtitle="Composite score (0–100) per launch = weighted milestone completion across workstreams, minus risk and gate penalties. Click a row to drill into the workstream breakdown."
      />
      <div className="px-10 py-6 space-y-6">
        <div className="grid grid-cols-5 gap-4">
          <Stat label="Portfolio avg" value={String(avg)} note="weighted composite" />
          <Stat label="Ready" value={String(summary.Ready)}    note="score ≥ 80" tone="green" />
          <Stat label="Tracking" value={String(summary.Tracking)} note="60–79"     tone="amber" />
          <Stat label="At risk" value={String(summary["At risk"])} note="40–59"    tone="red" />
          <Stat label="Behind" value={String(summary.Behind)}  note="< 40"        tone="red" />
        </div>

        <Card className="overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead className="bg-paper-2 border-b border-line text-left">
              <tr>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Launch</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Target</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Score</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Band</th>
                {workstreams.map((w) => (
                  <th key={w} className="p-3 font-mono uppercase text-[9px] tracking-widest text-mute text-center">
                    {w.split(" ")[0]}
                  </th>
                ))}
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute text-center">High risks</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((r) => (
                <tr key={r.launch_id} className="border-b border-line last:border-0 hover:bg-paper-2">
                  <td className="p-3">
                    <Link to={`/launches/${r.launch_id}`} className="font-mono text-primary hover:underline">
                      {r.launch_code}
                    </Link>
                    <div className="text-xs">{r.asset} · {r.country}</div>
                  </td>
                  <td className="p-3 font-mono text-xs">{r.target_launch_date ?? "—"}</td>
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-paper-3 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${r.composite_score}%`,
                            background: r.composite_score >= 80 ? "#2F7D4F"
                                      : r.composite_score >= 60 ? "#B8740A"
                                      : "#C8102E",
                          }}
                        />
                      </div>
                      <span className="font-display text-base">{r.composite_score.toFixed(0)}</span>
                    </div>
                  </td>
                  <td className="p-3">
                    <span className={`chip ${BAND_STYLE[r.band]}`}>{r.band}</span>
                  </td>
                  {workstreams.map((w) => {
                    const s = r.workstreams[w];
                    return (
                      <td key={w} className="p-3 text-center">
                        {s === null || s === undefined ? (
                          <span className="text-mute font-mono text-xs">—</span>
                        ) : (
                          <span
                            className="inline-block w-8 h-6 leading-6 rounded text-[10px] font-mono font-medium"
                            style={{
                              background: s >= 80 ? "#EDF5EF" : s >= 50 ? "#FAF1E0" : "#FBE8EB",
                              color:      s >= 80 ? "#2F7D4F" : s >= 50 ? "#B8740A" : "#C8102E",
                            }}
                          >
                            {Math.round(s)}
                          </span>
                        )}
                      </td>
                    );
                  })}
                  <td className="p-3 text-center font-mono text-sm">
                    {r.high_risks > 0 ? (
                      <span className="text-destructive font-bold">{r.high_risks}</span>
                    ) : (
                      <span className="text-mute">0</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <div className="text-xs text-mute-2 max-w-3xl">
          Composite formula: workstream completion (weighted 30/25/20/15/10/5 across Reg/Access/Commercial/Medical/Supply/Compliance)
          − 5 pts per open high-risk − 7 pts per failed readiness gate (L-180 / L-90 / L-30 / L+0).
        </div>
      </div>
    </>
  );
}

function Stat({ label, value, note, tone }: { label: string; value: string; note?: string; tone?: "green" | "amber" | "red" }) {
  const toneClass = tone === "green" ? "border-[#2F7D4F]/30 bg-[#EDF5EF]"
                  : tone === "amber" ? "border-[#B8740A]/30 bg-[#FAF1E0]"
                  : tone === "red"   ? "border-[#C8102E]/30 bg-[#FBE8EB]"
                  : "border-line bg-paper";
  return (
    <Card className={`p-4 ${toneClass}`}>
      <div className="font-mono text-[10px] uppercase tracking-widest text-mute">{label}</div>
      <div className="font-display text-3xl tracking-tight mt-1">{value}</div>
      {note && <div className="text-[10px] text-mute-2 mt-1">{note}</div>}
    </Card>
  );
}
