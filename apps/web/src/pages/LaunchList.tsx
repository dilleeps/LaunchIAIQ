import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { Launch } from "../lib/types";
import { PageHeader, RagChip } from "../components/PageHeader";
import { Input } from "../components/ui/input";
import { Select } from "../components/ui/select";
import { Button } from "../components/ui/button";

type Filters = {
  q: string;
  ta: string;
  phase: string;
  rag: string;
  region: string;
  type: string;
  hta: string;
};

const EMPTY: Filters = { q: "", ta: "", phase: "", rag: "", region: "", type: "", hta: "" };

export function LaunchList() {
  const { data } = useQuery({ queryKey: ["launches"], queryFn: () => api<Launch[]>("/launches") });
  const [f, setF] = useState<Filters>(EMPTY);
  const set = <K extends keyof Filters>(k: K, v: Filters[K]) => setF((s) => ({ ...s, [k]: v }));
  const reset = () => setF(EMPTY);
  const activeCount = Object.values(f).filter(Boolean).length;

  const opts = useMemo(() => {
    const tas = new Set<string>(), regions = new Set<string>(), types = new Set<string>(), htas = new Set<string>();
    for (const l of data || []) {
      if (l.asset.therapeutic_area) tas.add(l.asset.therapeutic_area);
      if (l.country.region) regions.add(l.country.region);
      if (l.launch_type) types.add(l.launch_type);
      if (l.hta_decision) htas.add(l.hta_decision);
    }
    return {
      tas: Array.from(tas).sort(),
      regions: Array.from(regions).sort(),
      types: Array.from(types).sort(),
      htas: Array.from(htas).sort(),
    };
  }, [data]);

  const filtered = useMemo(() => {
    return (data || []).filter((l) => {
      if (f.q) {
        const q = f.q.toLowerCase();
        if (
          !l.asset.brand_name.toLowerCase().includes(q) &&
          !l.country.name.toLowerCase().includes(q) &&
          !l.launch_code.toLowerCase().includes(q) &&
          !(l.asset.inn ?? "").toLowerCase().includes(q)
        ) return false;
      }
      if (f.ta && l.asset.therapeutic_area !== f.ta) return false;
      if (f.region && l.country.region !== f.region) return false;
      if (f.phase && l.launch_phase !== f.phase) return false;
      if (f.type && l.launch_type !== f.type) return false;
      if (f.rag && l.overall_rag !== f.rag) return false;
      if (f.hta && l.hta_decision !== f.hta) return false;
      return true;
    });
  }, [data, f]);

  return (
    <>
      <PageHeader eyebrow="Workspace" title="All launches." subtitle="One row per Asset × Country launch." />

      {/* Filter bar */}
      <div className="px-10 pt-4 pb-3 border-b border-line bg-paper-2">
        <div className="grid grid-cols-[1fr_auto_auto_auto_auto_auto_auto_auto] gap-3 items-end">
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Search</label>
            <Input
              placeholder="Asset, INN, country, launch code…"
              value={f.q}
              onChange={(e) => set("q", e.target.value)}
            />
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">TA</label>
            <Select value={f.ta} onChange={(e) => set("ta", e.target.value)}>
              <option value="">All</option>
              {opts.tas.map((t) => <option key={t}>{t}</option>)}
            </Select>
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Region</label>
            <Select value={f.region} onChange={(e) => set("region", e.target.value)}>
              <option value="">All</option>
              {opts.regions.map((r) => <option key={r}>{r}</option>)}
            </Select>
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Phase</label>
            <Select value={f.phase} onChange={(e) => set("phase", e.target.value)}>
              <option value="">All</option>
              <option>Pre-launch</option>
              <option>Launch</option>
              <option>Post-launch</option>
            </Select>
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Type</label>
            <Select value={f.type} onChange={(e) => set("type", e.target.value)}>
              <option value="">All</option>
              {opts.types.map((t) => <option key={t}>{t}</option>)}
            </Select>
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">RAG</label>
            <Select value={f.rag} onChange={(e) => set("rag", e.target.value)}>
              <option value="">All</option>
              <option>Green</option>
              <option>Amber</option>
              <option>Red</option>
            </Select>
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">HTA</label>
            <Select value={f.hta} onChange={(e) => set("hta", e.target.value)}>
              <option value="">All</option>
              {opts.htas.map((h) => <option key={h}>{h}</option>)}
            </Select>
          </div>
          <div>
            <Button variant="outline" onClick={reset} disabled={activeCount === 0}>
              Clear {activeCount > 0 ? `(${activeCount})` : ""}
            </Button>
          </div>
        </div>
        <div className="text-[10px] font-mono uppercase tracking-widest text-mute mt-3">
          Showing <b className="text-ink-2">{filtered.length}</b> of <b className="text-ink-2">{data?.length ?? 0}</b> launches
        </div>
      </div>

      <div className="px-10 py-6">
        <div className="border border-line rounded bg-paper overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-paper-2 border-b border-line text-left">
              <tr>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Code</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Asset</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Country</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Type</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Phase</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Target</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">HTA</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">RAG</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr><td colSpan={8} className="p-6 text-mute text-sm">No launches match these filters.</td></tr>
              )}
              {filtered.map((ln) => (
                <tr key={ln.id} className="border-b border-line last:border-0 hover:bg-paper-2">
                  <td className="p-3 font-mono">
                    <Link className="text-primary hover:underline" to={`/launches/${ln.id}`}>{ln.launch_code}</Link>
                  </td>
                  <td className="p-3">
                    {ln.asset.brand_name}
                    {ln.asset.therapeutic_area && (
                      <div className="text-[10px] text-mute font-mono uppercase tracking-wider">{ln.asset.therapeutic_area}</div>
                    )}
                  </td>
                  <td className="p-3">
                    {ln.country.name}
                    {ln.country.region && (
                      <div className="text-[10px] text-mute font-mono uppercase tracking-wider">{ln.country.region}</div>
                    )}
                  </td>
                  <td className="p-3 text-mute-2">{ln.launch_type}</td>
                  <td className="p-3 text-mute-2">{ln.launch_phase}</td>
                  <td className="p-3 font-mono text-xs">{ln.target_launch_date}</td>
                  <td className="p-3 text-mute-2 text-xs">{ln.hta_decision ?? "—"}</td>
                  <td className="p-3"><RagChip rag={ln.overall_rag} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
