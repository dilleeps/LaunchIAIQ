import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { RefreshCw, Plus, X } from "lucide-react";
import { api } from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { Card } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";

interface SyncResult {
  asset_id: string;
  asset_name: string;
  search_terms: string[];
  ingested_this_run: number;
  total_intel_records_matching: number;
  ran: { kind: string; ok: boolean; ingested: number; terms_tried: string[]; errors: string[] }[];
}

interface AssetTerms {
  asset_id: string;
  brand_name: string;
  inn: string | null;
  extra_terms: string[];
}

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
  const qc = useQueryClient();
  const [lastSync, setLastSync] = useState<SyncResult | null>(null);
  const [newTerm, setNewTerm] = useState("");

  const { data } = useQuery({
    queryKey: ["ci-asset", assetId],
    queryFn: () => api<AssetIntel>(`/competitive-intel/assets/${assetId}`),
  });
  const { data: terms } = useQuery({
    queryKey: ["asset-terms", assetId],
    queryFn: () => api<AssetTerms>(`/intel/sync-asset/${assetId}/terms`),
  });
  const sync = useMutation({
    mutationFn: () => api<SyncResult>(`/intel/sync-asset/${assetId}`, { method: "POST" }),
    onSuccess: (r) => {
      setLastSync(r);
      qc.invalidateQueries({ queryKey: ["ci-asset", assetId] });
    },
    onError: (err: Error) => {
      setLastSync({ asset_id: assetId, asset_name: "", search_terms: [], ingested_this_run: 0, total_intel_records_matching: 0,
        ran: [{ kind: "sync", ok: false, ingested: 0, terms_tried: [], errors: [String(err.message)] }] });
    },
  });
  const addTerm = useMutation({
    mutationFn: (t: string) =>
      api(`/intel/sync-asset/${assetId}/terms?term=${encodeURIComponent(t)}`, { method: "POST" }),
    onSuccess: () => { setNewTerm(""); qc.invalidateQueries({ queryKey: ["asset-terms", assetId] }); },
  });
  const removeTerm = useMutation({
    mutationFn: (t: string) => api(`/intel/sync-asset/${assetId}/terms/${encodeURIComponent(t)}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["asset-terms", assetId] }),
  });

  if (!data) return <div className="p-10 text-mute">Loading…</div>;

  return (
    <>
      <PageHeader
        eyebrow="Competitive intelligence"
        title={data.asset.brand_name}
        subtitle={`${data.asset.moa ?? ""} · ${data.asset.therapeutic_area ?? ""}`}
        right={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => sync.mutate()} disabled={sync.isPending}>
              <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${sync.isPending ? "animate-spin" : ""}`} />
              {sync.isPending ? "Syncing…" : "Sync intel"}
            </Button>
            <Link to="/competitive-intel" className="text-sm text-primary hover:underline self-center">← All assets</Link>
          </div>
        }
      />

      {lastSync && (
        <div className="px-10 pt-4">
          <div className={`border rounded-lg p-4 ${lastSync.ingested_this_run > 0 ? "border-[#2F7D4F]/30 bg-[#EDF5EF]" : "border-line bg-paper-2"}`}>
            <div className="flex items-start justify-between">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-mute mb-1">
                  Last sync · {lastSync.search_terms.length} term{lastSync.search_terms.length === 1 ? "" : "s"} fanned out
                </div>
                <div className="text-sm">
                  Ingested <b>{lastSync.ingested_this_run}</b> new record{lastSync.ingested_this_run === 1 ? "" : "s"} ·
                  total matching <b>{lastSync.total_intel_records_matching}</b>
                </div>
                <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
                  {lastSync.ran.map((r) => (
                    <div key={r.kind} className={`border rounded px-2 py-1.5 ${r.ok ? "border-line bg-paper" : "border-destructive/30 bg-destructive/5"}`}>
                      <div className="font-mono text-[10px] uppercase tracking-wider text-mute">{r.kind}</div>
                      <div className="mt-0.5">{r.ok ? `✓ ${r.ingested} ingested` : "✗ failed"}</div>
                      {r.errors?.length > 0 && (
                        <div className="text-[10px] text-destructive mt-1 truncate" title={r.errors.join("; ")}>
                          {r.errors[0]}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
              <button onClick={() => setLastSync(null)} className="text-mute hover:text-ink"><X className="w-4 h-4" /></button>
            </div>
          </div>
        </div>
      )}
      <div className="px-10 py-8 space-y-8">
        <section>
          <h2 className="font-mono text-[11px] uppercase tracking-widest text-mute mb-3">
            Search synonyms · drives market-intel fan-out
          </h2>
          <Card className="p-4">
            <div className="text-xs text-mute-2 mb-3">
              Each sync queries openFDA, ClinicalTrials.gov and DailyMed once per term below.
              Add research codes (TAK-861, PTG-300) or class names so pre-approval pipeline drugs match.
            </div>
            <div className="flex flex-wrap gap-2 mb-3">
              {terms?.brand_name && (
                <span className="px-2.5 py-1 bg-primary-soft text-primary rounded-full text-xs font-mono">
                  {terms.brand_name} <span className="text-[9px] uppercase tracking-wider opacity-60">brand</span>
                </span>
              )}
              {terms?.inn && terms.inn.toLowerCase() !== terms.brand_name.toLowerCase() && (
                <span className="px-2.5 py-1 bg-paper-2 border border-line rounded-full text-xs font-mono">
                  {terms.inn} <span className="text-[9px] uppercase tracking-wider text-mute">INN</span>
                </span>
              )}
              {terms?.extra_terms.map((t) => (
                <span key={t} className="px-2.5 py-1 bg-paper-2 border border-line rounded-full text-xs font-mono flex items-center gap-1.5">
                  {t}
                  <button onClick={() => removeTerm.mutate(t)} className="text-mute hover:text-destructive">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <Input
                value={newTerm}
                onChange={(e) => setNewTerm(e.target.value)}
                placeholder="Add a research code or synonym (e.g. TAK-861)"
                className="flex-1 text-sm"
                onKeyDown={(e) => { if (e.key === "Enter" && newTerm.trim()) { addTerm.mutate(newTerm.trim()); } }}
              />
              <Button size="sm" variant="outline" disabled={!newTerm.trim() || addTerm.isPending} onClick={() => addTerm.mutate(newTerm.trim())}>
                <Plus className="w-3.5 h-3.5 mr-1" />
                Add term
              </Button>
            </div>
          </Card>
        </section>

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
