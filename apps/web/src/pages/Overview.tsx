import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { Launch, OverviewStat } from "../lib/types";
import { PageHeader, RagChip } from "../components/PageHeader";
import { ImportPRD } from "../components/ImportPRD";

const fmtCurrency = (n: number, ccy: string) => {
  if (n >= 1e9) return `${(n / 1e9).toFixed(1)} B ${ccy}`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)} M ${ccy}`;
  return `${n.toLocaleString()} ${ccy}`;
};

export function Overview() {
  const { data: stats } = useQuery({
    queryKey: ["overview"],
    queryFn: () => api<OverviewStat>("/portfolio/overview"),
  });
  const { data: launches } = useQuery({
    queryKey: ["launches"],
    queryFn: () => api<Launch[]>("/launches"),
  });

  return (
    <>
      <PageHeader
        eyebrow="Portfolio · FY2026 — FY2027"
        title="Three assets. One cockpit."
        subtitle="Asset × Country launches tracked across regulatory, market access, medical, commercial and supply workstreams. Open dependencies surface upstream/downstream risk in one click."
        right={
          <div className="flex gap-2">
            <ImportPRD />
            <button className="px-3 py-2 bg-primary text-paper rounded text-sm hover:bg-primary-dark font-mono uppercase tracking-wider text-[11px]">+ New launch</button>
          </div>
        }
      />

      <section className="px-10 py-8 grid grid-cols-4 gap-6">
        <StatCard
          label="On-track launches"
          value={`${stats?.on_track_count ?? "—"} / ${stats?.total_launches ?? "—"}`}
          note="Green RAG today"
        />
        <StatCard
          label="Peak revenue (modelled)"
          value={stats ? fmtCurrency(stats.peak_revenue, stats.peak_revenue_currency) : "—"}
          note="Across 3-yr forecast horizon"
        />
        <StatCard
          label="High risks open"
          value={String(stats?.high_risks_open ?? "—")}
          note="Score ≥ 6 (L×I)"
          accent={!!stats?.high_risks_open && stats.high_risks_open > 0}
        />
        <StatCard
          label="Next milestone"
          value={stats?.next_milestone?.name ?? "—"}
          note={
            stats?.next_milestone
              ? `${stats.next_milestone.launch_code} · ${stats.next_milestone.target_date}`
              : "All caught up"
          }
        />
      </section>

      <section className="px-10 pb-12">
        <div className="font-mono text-[11px] uppercase tracking-widest text-mute mb-4">Active launches</div>
        <div className="grid grid-cols-3 gap-4">
          {launches?.map((ln) => (
            <Link
              key={ln.id}
              to={`/launches/${ln.id}`}
              className="border border-line rounded-lg p-5 hover:border-line-dark transition bg-paper"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="font-mono text-[11px] uppercase tracking-wider text-mute">{ln.launch_code}</span>
                <RagChip rag={ln.overall_rag} />
              </div>
              <div className="font-display text-xl tracking-tight">{ln.asset.brand_name}</div>
              <div className="text-mute-2 text-sm mt-1">
                {ln.country.name} · {ln.launch_type}
              </div>
              <div className="mt-4 pt-4 border-t border-line flex justify-between text-xs">
                <div>
                  <div className="text-mute font-mono uppercase tracking-wider text-[10px]">Target</div>
                  <div className="mt-0.5">{ln.target_launch_date ?? "—"}</div>
                </div>
                <div>
                  <div className="text-mute font-mono uppercase tracking-wider text-[10px]">Phase</div>
                  <div className="mt-0.5">{ln.launch_phase ?? "—"}</div>
                </div>
                <div>
                  <div className="text-mute font-mono uppercase tracking-wider text-[10px]">HTA</div>
                  <div className="mt-0.5">{ln.hta_decision ?? "—"}</div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </>
  );
}

function StatCard({ label, value, note, accent }: { label: string; value: string; note?: string; accent?: boolean }) {
  return (
    <div className={`border rounded-lg p-5 ${accent ? "border-primary bg-primary-soft" : "border-line bg-paper"}`}>
      <div className="font-mono text-[10px] uppercase tracking-widest text-mute">{label}</div>
      <div className="font-display text-3xl tracking-tight mt-2 leading-tight">{value}</div>
      {note && <div className="text-xs text-mute-2 mt-2">{note}</div>}
    </div>
  );
}
