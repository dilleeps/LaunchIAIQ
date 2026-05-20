import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { Card } from "../components/ui/card";

interface PortfolioRow {
  asset_id: string;
  brand_name: string;
  therapeutic_area: string | null;
  competitor_count: number;
  intel_90d: number;
}

interface Competitor {
  id: string;
  competitor_name: string;
  company: string | null;
  moa: string | null;
  stage: string | null;
  notes: string | null;
}

interface IntelRecord {
  id: string;
  country_code: string | null;
  record_type: string;
  title: string;
  occurred_at: string | null;
}

interface AssetIntel {
  asset: { id: string; brand_name: string; inn: string | null; therapeutic_area: string | null; moa: string | null };
  competitors: Competitor[];
  live_intel: IntelRecord[];
}

export function CompetitiveIntel() {
  const { assetId } = useParams();
  return assetId ? <AssetDetail assetId={assetId} /> : <PortfolioView />;
}

function PortfolioView() {
  const { data } = useQuery({
    queryKey: ["ci-portfolio"],
    queryFn: () => api<PortfolioRow[]>("/competitive-intel/portfolio"),
  });
  return (
    <>
      <PageHeader
        eyebrow="Competitive intelligence"
        title="Know the field."
        subtitle="Per-asset competitor map, merged with live market-intel signals from the free-source connector pipeline (openFDA, ClinicalTrials.gov, DailyMed, WHO GHO, CMS Open Payments)."
      />
      <div className="px-10 py-8">
        <div className="grid grid-cols-3 gap-4">
          {data?.map((row) => (
            <Link
              key={row.asset_id}
              to={`/competitive-intel/${row.asset_id}`}
              className="block border border-line rounded-lg p-5 bg-paper hover:border-line-dark transition"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="font-display text-xl tracking-tight">{row.brand_name}</div>
                <span className="chip rag-Pending">{row.therapeutic_area ?? "—"}</span>
              </div>
              <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-line">
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-widest text-mute">Competitors</div>
                  <div className="font-display text-2xl tracking-tight mt-1">{row.competitor_count}</div>
                </div>
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-widest text-mute">Intel · 90d</div>
                  <div className="font-display text-2xl tracking-tight mt-1">{row.intel_90d}</div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </>
  );
}

function AssetDetail({ assetId }: { assetId: string }) {
  const { data } = useQuery({
    queryKey: ["ci-asset", assetId],
    queryFn: () => api<AssetIntel>(`/competitive-intel/assets/${assetId}`),
  });
  if (!data) return <div className="p-10 text-mute">Loading…</div>;

  return (
    <>
      <PageHeader
        eyebrow="Competitive intelligence"
        title={data.asset.brand_name}
        subtitle={`${data.asset.moa ?? ""} · ${data.asset.therapeutic_area ?? ""}`}
        right={<Link to="/competitive-intel" className="text-sm text-primary hover:underline">← All assets</Link>}
      />
      <div className="px-10 py-8 space-y-8">
        <section>
          <h2 className="font-mono text-[11px] uppercase tracking-widest text-mute mb-3">Competitive set</h2>
          <Card className="overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-paper-2 border-b border-line text-left">
                <tr>
                  <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Competitor</th>
                  <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Company</th>
                  <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">MoA</th>
                  <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Stage</th>
                </tr>
              </thead>
              <tbody>
                {data.competitors.map((c) => (
                  <tr key={c.id} className="border-b border-line last:border-0">
                    <td className="p-3 font-medium">{c.competitor_name}</td>
                    <td className="p-3 text-mute-2">{c.company ?? "—"}</td>
                    <td className="p-3 text-mute-2">{c.moa ?? "—"}</td>
                    <td className="p-3"><span className="chip rag-Pending">{c.stage ?? "—"}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </section>
        <section>
          <h2 className="font-mono text-[11px] uppercase tracking-widest text-mute mb-3">Live market intelligence (matched by brand or TA)</h2>
          {data.live_intel.length === 0 ? (
            <p className="text-sm text-mute">No live records yet. Trigger a connector sync from Settings to populate.</p>
          ) : (
            <div className="space-y-2">
              {data.live_intel.map((r) => (
                <div key={r.id} className="border border-line rounded p-3 bg-paper flex items-center gap-3">
                  <span className="chip rag-Pending">{r.record_type}</span>
                  <span className="font-mono text-[11px] uppercase text-mute">{r.country_code}</span>
                  <span className="font-mono text-[11px] text-mute">{r.occurred_at?.slice(0, 10)}</span>
                  <span className="flex-1">{r.title}</span>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </>
  );
}
