import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { addDays, differenceInDays, format, parseISO, startOfMonth } from "date-fns";
import { api } from "../lib/api";
import type { Launch } from "../lib/types";
import { PageHeader, RagChip } from "../components/PageHeader";
import { Input } from "../components/ui/input";
import { Select } from "../components/ui/select";
import { Button } from "../components/ui/button";

interface MilestoneRow {
  id: string;
  launch_id: string;
  name: string;
  target_date?: string | null;
  status: string;
  is_gate: boolean;
}

// Phase palette — each segment of a launch's lifecycle gets a distinct tint
const PHASE_COLORS = {
  filing:     "#9CA3AF",   // grey — pre-approval prep
  approved:   "#165D59",   // primary teal — approved, working access
  htaCleared: "#B8740A",   // amber — HTA negotiation
  launched:   "#2F7D4F",   // green — commercial launch window
  postLaunch: "#C8102E",   // accent red — post-launch / variance watch
};

const PHASE_LABELS: Record<string, string> = {
  filing: "Filing",
  approved: "Approved",
  htaCleared: "Reimbursed",
  launched: "Launched",
  postLaunch: "Post-launch",
};

type FilterState = {
  q: string;
  ta: string;
  phase: string;
  rag: string;
  region: string;
  type: string;
  window: string; // 6m | 12m | 24m | all
};

const EMPTY_FILTERS: FilterState = {
  q: "", ta: "", phase: "", rag: "", region: "", type: "", window: "24m",
};

export function Timeline() {
  const [filters, setFilters] = useState<FilterState>(EMPTY_FILTERS);
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

  const setF = <K extends keyof FilterState>(k: K, v: FilterState[K]) =>
    setFilters((f) => ({ ...f, [k]: v }));
  const reset = () => setFilters(EMPTY_FILTERS);
  const activeCount = Object.entries(filters).filter(
    ([k, v]) => v && !(k === "window" && v === "24m")
  ).length;

  const { data: launches } = useQuery({
    queryKey: ["launches"],
    queryFn: () => api<Launch[]>("/launches"),
  });
  const { data: upcoming } = useQuery({
    queryKey: ["upcoming-milestones-365"],
    queryFn: () => api<MilestoneRow[]>("/milestones/upcoming?days=365"),
  });

  const windowDays = filters.window === "6m" ? 180 : filters.window === "12m" ? 365 : filters.window === "all" ? 1095 : 720;

  const { startDate, days, monthMarkers, todayPct } = useMemo(() => {
    const today = new Date();
    const start = startOfMonth(addDays(today, -90));
    const end = addDays(start, windowDays);
    const totalDays = differenceInDays(end, start);
    const markers: { x: number; label: string; isQuarter: boolean }[] = [];
    let cursor = startOfMonth(start);
    while (cursor < end) {
      const isQuarter = cursor.getMonth() % 3 === 0;
      markers.push({
        x: (differenceInDays(cursor, start) / totalDays) * 100,
        label: isQuarter ? format(cursor, "QQQ yy").toUpperCase() : format(cursor, "MMM").toLowerCase(),
        isQuarter,
      });
      cursor = startOfMonth(addDays(cursor, 35));
    }
    return {
      startDate: start,
      days: totalDays,
      monthMarkers: markers,
      todayPct: (differenceInDays(today, start) / totalDays) * 100,
    };
  }, [windowDays]);

  const filterOptions = useMemo(() => {
    const tas = new Set<string>(), regions = new Set<string>(), types = new Set<string>();
    for (const l of launches || []) {
      if (l.asset.therapeutic_area) tas.add(l.asset.therapeutic_area);
      if (l.country.region) regions.add(l.country.region);
      if (l.launch_type) types.add(l.launch_type);
    }
    return {
      tas: Array.from(tas).sort(),
      regions: Array.from(regions).sort(),
      types: Array.from(types).sort(),
    };
  }, [launches]);

  const grouped = useMemo(() => {
    const filtered = (launches || []).filter((l) => {
      if (filters.q) {
        const q = filters.q.toLowerCase();
        if (
          !l.asset.brand_name.toLowerCase().includes(q) &&
          !l.country.name.toLowerCase().includes(q) &&
          !l.launch_code.toLowerCase().includes(q)
        ) return false;
      }
      if (filters.ta && l.asset.therapeutic_area !== filters.ta) return false;
      if (filters.phase && l.launch_phase !== filters.phase) return false;
      if (filters.rag && l.overall_rag !== filters.rag) return false;
      if (filters.region && l.country.region !== filters.region) return false;
      if (filters.type && l.launch_type !== filters.type) return false;
      return true;
    });
    const map = new Map<string, { asset: Launch["asset"]; launches: Launch[] }>();
    for (const l of filtered) {
      const k = l.asset.id;
      if (!map.has(k)) map.set(k, { asset: l.asset, launches: [] });
      map.get(k)!.launches.push(l);
    }
    return Array.from(map.values()).sort((a, b) => a.asset.brand_name.localeCompare(b.asset.brand_name));
  }, [launches, filters]);

  function pct(d: Date) { return (differenceInDays(d, startDate) / days) * 100; }

  return (
    <>
      <PageHeader
        eyebrow="Portfolio timeline"
        title="Phase-segmented launch view."
        subtitle="Each launch sweeps through five visual phases — filing, approval, reimbursement, launch, post-launch. Gate milestones are starred on the bar; today is the teal line. Grouped by asset."
      />

      {/* Filter bar */}
      <div className="px-10 pt-4 pb-2 border-b border-line bg-paper-2">
        <div className="grid grid-cols-[1fr_auto_auto_auto_auto_auto_auto_auto] gap-3 items-end">
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Search</label>
            <Input
              placeholder="Asset, country, launch code…"
              value={filters.q}
              onChange={(e) => setF("q", e.target.value)}
            />
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">TA</label>
            <Select value={filters.ta} onChange={(e) => setF("ta", e.target.value)}>
              <option value="">All</option>
              {filterOptions.tas.map((t) => <option key={t}>{t}</option>)}
            </Select>
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Region</label>
            <Select value={filters.region} onChange={(e) => setF("region", e.target.value)}>
              <option value="">All</option>
              {filterOptions.regions.map((r) => <option key={r}>{r}</option>)}
            </Select>
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Phase</label>
            <Select value={filters.phase} onChange={(e) => setF("phase", e.target.value)}>
              <option value="">All</option>
              <option>Pre-launch</option>
              <option>Launch</option>
              <option>Post-launch</option>
            </Select>
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Type</label>
            <Select value={filters.type} onChange={(e) => setF("type", e.target.value)}>
              <option value="">All</option>
              {filterOptions.types.map((t) => <option key={t}>{t}</option>)}
            </Select>
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">RAG</label>
            <Select value={filters.rag} onChange={(e) => setF("rag", e.target.value)}>
              <option value="">All</option>
              <option>Green</option>
              <option>Amber</option>
              <option>Red</option>
            </Select>
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Window</label>
            <Select value={filters.window} onChange={(e) => setF("window", e.target.value)}>
              <option value="6m">6 mo</option>
              <option value="12m">12 mo</option>
              <option value="24m">24 mo</option>
              <option value="all">3 yr</option>
            </Select>
          </div>
          <div>
            <Button variant="outline" onClick={reset} disabled={activeCount === 0}>
              Clear {activeCount > 0 ? `(${activeCount})` : ""}
            </Button>
          </div>
        </div>
      </div>

      <div className="px-10 py-6">
        {/* Legend */}
        <div className="flex items-center gap-3 mb-4 text-xs font-mono uppercase tracking-wider">
          {Object.entries(PHASE_COLORS).map(([k, c]) => (
            <div key={k} className="flex items-center gap-1.5">
              <span className="w-4 h-3 rounded-sm" style={{ background: c }} />
              <span className="text-mute-2">{PHASE_LABELS[k]}</span>
            </div>
          ))}
          <div className="ml-4 flex items-center gap-1.5">
            <span className="text-primary">★</span>
            <span className="text-mute-2">gate milestone</span>
          </div>
        </div>

        <div className="border border-line rounded-lg bg-paper overflow-hidden">
          {/* Header bar with quarter labels */}
          <div className="relative h-9 border-b border-line bg-paper-2 grid" style={{ gridTemplateColumns: "300px 1fr 140px" }}>
            <div className="px-4 flex items-center font-mono text-[10px] uppercase tracking-widest text-mute">Launch</div>
            <div className="relative">
              {monthMarkers.map((m, i) => (
                <div
                  key={i}
                  className={`absolute top-0 h-full border-l ${m.isQuarter ? "border-line-dark" : "border-line"} text-[10px] font-mono uppercase tracking-wider pl-1 pt-2.5`}
                  style={{
                    left: `${m.x}%`,
                    color: m.isQuarter ? "#333" : "#A8A8A8",
                  }}
                >
                  {m.label}
                </div>
              ))}
            </div>
            <div className="px-3 flex items-center justify-end font-mono text-[10px] uppercase tracking-widest text-mute">
              Reg → Launch
            </div>
          </div>

          {/* Today line — extends through all rows */}
          <div className="relative">
            <div
              className="absolute z-20 w-px bg-primary pointer-events-none"
              style={{
                left: `calc(300px + ${todayPct}% * (100% - 440px) / 100)`,
                top: 0, bottom: 0,
              }}
            >
              <span className="absolute -top-3 left-1 text-[9px] font-mono text-primary uppercase tracking-wider bg-paper px-1 border border-line rounded-sm">
                Today
              </span>
            </div>

            {grouped.map(({ asset, launches: lns }, idx) => {
              const isCollapsed = collapsed[asset.id];
              return (
                <div key={asset.id}>
                  {/* Asset header row */}
                  <div
                    className={`grid items-center bg-paper-3 border-y border-line cursor-pointer hover:bg-paper-2`}
                    style={{ gridTemplateColumns: "300px 1fr 140px" }}
                    onClick={() => setCollapsed((c) => ({ ...c, [asset.id]: !c[asset.id] }))}
                  >
                    <div className="px-4 py-2 flex items-center gap-2">
                      <span className="text-mute font-mono text-xs">{isCollapsed ? "▸" : "▾"}</span>
                      <div className="font-display text-base tracking-tight">{asset.brand_name}</div>
                      <span className="font-mono text-[10px] uppercase tracking-wider text-mute">
                        {asset.therapeutic_area} · {lns.length} launches
                      </span>
                    </div>
                    <div></div>
                    <div></div>
                  </div>

                  {!isCollapsed && lns.map((ln) => {
                    const reg = ln.reg_approval_date ? parseISO(ln.reg_approval_date) : null;
                    const tgt = ln.target_launch_date ? parseISO(ln.target_launch_date) : null;
                    if (!reg || !tgt) return null;

                    // Define phase boundaries
                    const filingStart = pct(addDays(reg, -180));
                    const filingEnd = pct(reg);
                    const approvedEnd = pct(addDays(reg, 60));         // ~2 months for HTA prep
                    const htaEnd = pct(addDays(tgt, -30));              // 30 days before launch
                    const launchedEnd = pct(addDays(tgt, 90));          // 90-day post-FCS launch window
                    const postEnd = pct(addDays(tgt, 365));             // 1 yr post-launch

                    const gates = (upcoming || []).filter(
                      (m) => m.launch_id === ln.id && m.is_gate && m.target_date
                    );

                    return (
                      <div
                        key={ln.id}
                        className="grid items-center border-b border-line last:border-0 hover:bg-paper-2 transition"
                        style={{ gridTemplateColumns: "300px 1fr 140px" }}
                      >
                        <div className="px-4 py-3 flex items-center gap-3 border-r border-line">
                          <RagChip rag={ln.overall_rag} />
                          <div className="min-w-0">
                            <Link to={`/launches/${ln.id}`} className="text-sm font-medium hover:underline truncate block">
                              {ln.country.name}
                            </Link>
                            <div className="text-[10px] text-mute font-mono uppercase tracking-wider">
                              {ln.launch_code} · {ln.launch_type}
                            </div>
                          </div>
                        </div>

                        <div className="relative h-12">
                          {/* Filing prep */}
                          <Segment left={filingStart} right={filingEnd} color={PHASE_COLORS.filing} label="filing" />
                          {/* Approval window */}
                          <Segment left={filingEnd} right={approvedEnd} color={PHASE_COLORS.approved} label="approval" />
                          {/* HTA / reimbursement */}
                          <Segment left={approvedEnd} right={htaEnd} color={PHASE_COLORS.htaCleared} label="reimbursement" />
                          {/* Launch window */}
                          <Segment left={htaEnd} right={launchedEnd} color={PHASE_COLORS.launched} label="launch" prominent />
                          {/* Post-launch */}
                          <Segment left={launchedEnd} right={postEnd} color={PHASE_COLORS.postLaunch} label="post-launch" muted />

                          {/* FCS marker */}
                          <div
                            className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-paper border-2 border-ink z-10"
                            style={{ left: `${pct(tgt)}%`, transform: `translate(-50%, -50%)` }}
                            title={`FCS: ${ln.target_launch_date}`}
                          />

                          {/* Gate stars */}
                          {gates.map((g) => {
                            const x = pct(parseISO(g.target_date!));
                            return (
                              <div
                                key={g.id}
                                className="absolute top-1/2 -translate-y-1/2 text-primary text-base z-10"
                                style={{ left: `${x}%`, transform: `translate(-50%, -55%)` }}
                                title={`${g.name} · ${g.target_date}`}
                              >
                                ★
                              </div>
                            );
                          })}
                        </div>

                        <div className="px-3 py-3 text-[10px] font-mono text-mute-2 leading-tight border-l border-line">
                          <div>{format(reg, "dd MMM yy")}</div>
                          <div className="text-ink-2">→ {format(tgt, "dd MMM yy")}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              );
            })}
            {grouped.length === 0 && (
              <div className="p-6 text-mute text-sm">No launches match this filter.</div>
            )}
          </div>
        </div>

        {/* Reading guide */}
        <div className="mt-4 text-xs text-mute-2 max-w-3xl leading-relaxed">
          Bars compress the multi-year launch lifecycle into a single visual: <b>grey</b> = filing prep,
          <b className="text-[#165D59]"> teal</b> = regulatory approval window, <b className="text-[#B8740A]">amber</b> = HTA / reimbursement,
          <b className="text-[#2F7D4F]"> green</b> = active launch (the dark dot is First Commercial Sale),
          <b className="text-[#C8102E]"> red</b> = post-launch performance window. Stars are gate milestones — click a row to drill into its PRD, KPIs and risks.
        </div>
      </div>
    </>
  );
}

function Segment({
  left, right, color, label, prominent, muted,
}: { left: number; right: number; color: string; label: string; prominent?: boolean; muted?: boolean }) {
  const width = Math.max(0, right - left);
  if (width === 0) return null;
  return (
    <div
      className="absolute h-5"
      style={{
        top: prominent ? "calc(50% - 14px)" : muted ? "calc(50% - 5px)" : "calc(50% - 10px)",
        height: prominent ? 28 : muted ? 10 : 20,
        left: `${left}%`,
        width: `${width}%`,
        background: color,
        opacity: muted ? 0.45 : 1,
        borderRadius: 3,
      }}
      title={label}
    />
  );
}
