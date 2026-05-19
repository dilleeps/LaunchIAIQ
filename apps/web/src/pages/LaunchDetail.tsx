import React, { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Button } from "../components/ui/button";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";
import type {
  DependencyEdge,
  Forecast,
  KPI,
  Launch,
  MarketIntel,
  Milestone,
  PRD,
  Risk,
} from "../lib/types";
import { PageHeader, RagChip } from "../components/PageHeader";

const tabs = ["PRD", "Milestones", "Risks", "KPIs", "Forecast", "Market Pulse", "Dependencies"] as const;
type Tab = (typeof tabs)[number];

export function LaunchDetail() {
  const { id } = useParams();
  const [tab, setTab] = useState<Tab>("PRD");
  const { data: launch } = useQuery({
    queryKey: ["launch", id],
    queryFn: () => api<Launch>(`/launches/${id}`),
    enabled: !!id,
  });

  if (!launch) return <div className="p-10 text-mute">Loading…</div>;

  return (
    <>
      <PageHeader
        eyebrow={`${launch.launch_code} · ${launch.country.name} · ${launch.country.hta_body ?? ""}`}
        title={launch.asset.brand_name}
        subtitle={`${launch.asset.therapeutic_area ?? ""} · ${launch.launch_type ?? ""} · ${launch.launch_phase ?? ""}`}
        right={<RagChip rag={launch.overall_rag} />}
      />
      <div className="border-b border-line px-10">
        <div className="flex gap-6">
          {tabs.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`py-3 text-sm font-mono uppercase tracking-wider border-b-2 ${
                tab === t ? "border-primary text-primary" : "border-transparent text-mute hover:text-ink-2"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
      <div className="px-10 py-8">
        {tab === "PRD" && <PRDTab launchId={launch.id} />}
        {tab === "Milestones" && <MilestonesTab launchId={launch.id} />}
        {tab === "Risks" && <RisksTab launchId={launch.id} />}
        {tab === "KPIs" && <KPIsTab launchId={launch.id} />}
        {tab === "Forecast" && <ForecastTab launchId={launch.id} />}
        {tab === "Market Pulse" && <MarketPulseTab brand={launch.asset.brand_name} country={launch.country.code} ta={launch.asset.therapeutic_area} />}
        {tab === "Dependencies" && <DependenciesTab launchId={launch.id} />}
      </div>
    </>
  );
}

function PRDTab({ launchId }: { launchId: string }) {
  const { data: prd } = useQuery({
    queryKey: ["prd", launchId],
    queryFn: () => api<PRD>(`/launches/${launchId}/prd`),
  });
  if (!prd) return <div className="text-mute">Loading PRD…</div>;
  return (
    <div className="space-y-8">
      <div className="font-mono text-[11px] uppercase tracking-widest text-mute">PRD v{prd.current_version}</div>
      {Object.entries(prd.payload).map(([section, fields]) => (
        <section key={section} className="border border-line rounded-lg p-6 bg-paper">
          <h2 className="font-display text-xl tracking-tight mb-4 capitalize">{section.replace(/_/g, " ")}</h2>
          <dl className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
            {Object.entries(fields as Record<string, any>).map(([k, v]) => (
              <div key={k}>
                <dt className="font-mono text-[10px] uppercase tracking-wider text-mute mb-1">{k.replace(/_/g, " ")}</dt>
                <dd>{String(v ?? "—")}</dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
    </div>
  );
}

function MilestonesTab({ launchId }: { launchId: string }) {
  const { data } = useQuery({
    queryKey: ["ms", launchId],
    queryFn: () => api<Milestone[]>(`/launches/${launchId}/milestones`),
  });
  return (
    <table className="w-full border border-line rounded text-sm bg-paper">
      <thead className="bg-paper-2 border-b border-line text-left">
        <tr>
          <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Target</th>
          <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Milestone</th>
          <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Status</th>
          <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Weight</th>
        </tr>
      </thead>
      <tbody>
        {data?.map((m) => (
          <tr key={m.id} className="border-b border-line last:border-0">
            <td className="p-3 font-mono text-xs">{m.target_date}</td>
            <td className="p-3">{m.is_gate && <span className="text-primary mr-1">★</span>}{m.name}</td>
            <td className="p-3 text-mute-2">{m.status}</td>
            <td className="p-3 font-mono text-xs">{m.weight}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function RisksTab({ launchId }: { launchId: string }) {
  const { data } = useQuery({
    queryKey: ["risks", launchId],
    queryFn: () => api<Risk[]>(`/risks?launch_id=${launchId}`),
  });
  const [aiSummary, setAiSummary] = React.useState<string | null>(null);
  const summarize = useMutation({
    mutationFn: () =>
      api<{ summary: string; source: string }>("/assistant/summarize-risks", {
        method: "POST",
        body: JSON.stringify({ launch_id: launchId }),
      }),
    onSuccess: (r) => setAiSummary(r.summary),
  });
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="text-sm text-mute-2">{data?.length ?? 0} risks linked to this launch.</div>
        <Button size="sm" variant="outline" onClick={() => summarize.mutate()} disabled={summarize.isPending}>
          {summarize.isPending ? "Thinking…" : "✦ AI summary"}
        </Button>
      </div>
      {aiSummary && (
        <div className="border-l-2 border-primary bg-primary-soft/30 p-4 rounded">
          <div className="font-mono text-[10px] uppercase tracking-widest text-primary mb-2">AI summary</div>
          <div className="text-sm whitespace-pre-line">{aiSummary}</div>
        </div>
      )}
      {data?.length === 0 && <div className="text-mute">No risks linked to this launch.</div>}
      {data?.map((r) => (
        <div key={r.id} className="border border-line rounded p-4 bg-paper">
          <div className="flex items-center gap-3 mb-2">
            <span className={`chip ${r.score >= 6 ? "rag-Red" : r.score >= 4 ? "rag-Amber" : "rag-Green"}`}>Score {r.score}</span>
            <span className="font-mono text-[11px] uppercase tracking-wider text-mute">{r.category}</span>
            <span className="font-mono text-[11px] uppercase tracking-wider text-mute">L:{r.likelihood} · I:{r.impact}</span>
          </div>
          <div className="font-medium">{r.description}</div>
          {r.mitigation && <div className="text-sm text-mute-2 mt-2">Mitigation: {r.mitigation}</div>}
        </div>
      ))}
    </div>
  );
}

function KPIsTab({ launchId }: { launchId: string }) {
  const { data } = useQuery({
    queryKey: ["kpis", launchId],
    queryFn: () => api<KPI[]>(`/launches/${launchId}/kpis`),
  });
  return (
    <table className="w-full border border-line text-sm bg-paper">
      <thead className="bg-paper-2 border-b border-line text-left">
        <tr>
          <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Category</th>
          <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">KPI</th>
          <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Unit</th>
          <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Target</th>
        </tr>
      </thead>
      <tbody>
        {data?.map((k) => (
          <tr key={k.id} className="border-b border-line last:border-0">
            <td className="p-3">{k.category}</td>
            <td className="p-3">{k.name}</td>
            <td className="p-3 font-mono text-xs">{k.unit ?? "—"}</td>
            <td className="p-3 font-mono text-xs">{k.target ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ForecastTab({ launchId }: { launchId: string }) {
  const { data } = useQuery({
    queryKey: ["forecast", launchId],
    queryFn: () => api<Forecast[]>(`/launches/${launchId}/forecast`),
  });
  const current = data?.find((f) => f.is_current) ?? data?.[0];
  if (!current) return <div className="text-mute">No forecast yet.</div>;
  const rev = (p?: number | null, pr?: number | null) =>
    p && pr ? `${((p * pr) / 1e6).toFixed(1)} M ${current.currency}` : "—";
  return (
    <div className="grid grid-cols-3 gap-4">
      {[
        { yr: "Y1", p: current.y1_patients, pr: current.y1_net_price },
        { yr: "Y2", p: current.y2_patients, pr: current.y2_net_price },
        { yr: "Y3", p: current.y3_patients, pr: current.y3_net_price },
      ].map((c) => (
        <div key={c.yr} className="border border-line rounded p-5 bg-paper">
          <div className="font-mono text-[11px] uppercase tracking-widest text-mute mb-2">{c.yr}</div>
          <div className="font-display text-3xl tracking-tight">{rev(c.p, c.pr)}</div>
          <div className="text-mute-2 text-sm mt-2">{c.p?.toLocaleString()} patients · {current.currency} {c.pr?.toLocaleString()} / patient</div>
        </div>
      ))}
    </div>
  );
}

function MarketPulseTab({ brand, country, ta }: { brand: string; country: string; ta?: string | null }) {
  const { data } = useQuery({
    queryKey: ["intel", brand, country, ta],
    queryFn: () =>
      api<MarketIntel[]>(
        `/intel/records?country_code=${country}${ta ? `&therapeutic_area=${encodeURIComponent(ta)}` : ""}`
      ),
  });
  return (
    <div className="space-y-3">
      <div className="text-mute text-sm">Sourced from openFDA, ClinicalTrials.gov, DailyMed and HTA bodies (all free APIs).</div>
      {data?.length === 0 && <div className="text-mute">No intel records yet. Run an integration sync from Settings.</div>}
      {data?.map((r) => (
        <div key={r.id} className="border border-line rounded p-4 bg-paper">
          <div className="flex items-center gap-3 mb-1">
            <span className="chip rag-Pending">{r.record_type}</span>
            <span className="font-mono text-[11px] uppercase tracking-wider text-mute">{r.country_code}</span>
            {r.occurred_at && <span className="font-mono text-[11px] text-mute">{r.occurred_at.slice(0, 10)}</span>}
          </div>
          <div className="font-medium">{r.title}</div>
        </div>
      ))}
    </div>
  );
}

function DependenciesTab({ launchId }: { launchId: string }) {
  const { data } = useQuery({
    queryKey: ["downstream", launchId],
    queryFn: () => api<DependencyEdge[]>(`/launches/${launchId}/downstream`),
  });
  return (
    <div>
      <div className="text-mute text-sm mb-4">Recursive walk of typed cross-launch dependencies. Phase 2 will visualise this as a force-directed graph.</div>
      <table className="w-full border border-line text-sm bg-paper">
        <thead className="bg-paper-2 border-b border-line text-left">
          <tr>
            <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Depth</th>
            <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Link</th>
            <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Target</th>
          </tr>
        </thead>
        <tbody>
          {data?.length === 0 && (
            <tr><td colSpan={3} className="p-4 text-mute">No downstream dependencies.</td></tr>
          )}
          {data?.map((d, i) => (
            <tr key={i} className="border-b border-line last:border-0">
              <td className="p-3 font-mono text-xs">{d.depth}</td>
              <td className="p-3"><span className="chip rag-Pending">{d.link_type}</span></td>
              <td className="p-3 font-mono text-xs">{d.target_type}:{d.target_id.slice(0, 8)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
