import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { addDays, differenceInDays, format, parseISO, startOfMonth } from "date-fns";
import { api } from "../lib/api";
import type { Launch } from "../lib/types";
import { PageHeader, RagChip } from "../components/PageHeader";

interface MilestoneRow {
  id: string;
  launch_id: string;
  name: string;
  target_date?: string | null;
  status: string;
  is_gate: boolean;
}

const RAG_BAR: Record<string, string> = {
  Green: "#2F7D4F",
  Amber: "#B8740A",
  Red: "#C8102E",
};

export function Timeline() {
  const { data: launches } = useQuery({ queryKey: ["launches"], queryFn: () => api<Launch[]>("/launches") });
  const { data: upcoming } = useQuery({
    queryKey: ["upcoming-milestones-365"],
    queryFn: () => api<MilestoneRow[]>("/milestones/upcoming?days=365"),
  });

  const { startDate, endDate, monthMarkers, days } = useMemo(() => {
    const today = new Date();
    const start = startOfMonth(addDays(today, -30));
    const end = addDays(start, 545); // ~18 months
    const totalDays = differenceInDays(end, start);
    const markers: { x: number; label: string }[] = [];
    let cursor = start;
    while (cursor < end) {
      markers.push({ x: (differenceInDays(cursor, start) / totalDays) * 100, label: format(cursor, "MMM yy") });
      cursor = addDays(startOfMonth(addDays(cursor, 35)), 0);
    }
    return { startDate: start, endDate: end, monthMarkers: markers, days: totalDays };
  }, []);

  const todayPct = (differenceInDays(new Date(), startDate) / days) * 100;

  const rows = (launches || []).map((ln) => {
    const t = ln.target_launch_date ? parseISO(ln.target_launch_date) : null;
    const r = ln.reg_approval_date ? parseISO(ln.reg_approval_date) : null;
    const left = r ? (differenceInDays(r, startDate) / days) * 100 : 0;
    const right = t ? (differenceInDays(t, startDate) / days) * 100 : left + 4;
    const width = Math.max(2, right - left);
    const launchGates = (upcoming || []).filter((m) => m.launch_id === ln.id && m.is_gate && m.target_date);
    return { ln, left, width, launchGates };
  });

  return (
    <>
      <PageHeader
        eyebrow="Portfolio timeline"
        title="Critical path."
        subtitle="Regulatory approvals (start of bar) → target launch date (end). Gate milestones marked ★. Today indicated by vertical line."
      />
      <div className="px-10 py-6">
        <div className="border border-line rounded-lg bg-paper overflow-hidden">
          {/* Header */}
          <div className="relative h-10 border-b border-line bg-paper-2">
            {monthMarkers.map((m, i) => (
              <div
                key={i}
                className="absolute top-0 h-full border-l border-line text-[10px] font-mono uppercase tracking-wider text-mute pl-1 pt-2"
                style={{ left: `${m.x}%`, width: "8%" }}
              >
                {m.label}
              </div>
            ))}
          </div>
          {/* Rows */}
          <div className="relative">
            {/* Today line */}
            <div
              className="absolute top-0 bottom-0 w-px bg-primary/60 z-10"
              style={{ left: `${todayPct}%` }}
              title="Today"
            >
              <span className="absolute -top-3 -translate-x-1/2 text-[9px] font-mono text-primary uppercase tracking-wider bg-paper px-1">Today</span>
            </div>
            {rows.map(({ ln, left, width, launchGates }) => (
              <div key={ln.id} className="relative h-14 border-b border-line last:border-0 grid" style={{ gridTemplateColumns: "260px 1fr" }}>
                <div className="px-4 py-3 flex items-center gap-3 border-r border-line">
                  <RagChip rag={ln.overall_rag} />
                  <div>
                    <Link to={`/launches/${ln.id}`} className="text-sm hover:underline">{ln.asset.brand_name}</Link>
                    <div className="text-xs text-mute-2">{ln.launch_code} · {ln.country.name}</div>
                  </div>
                </div>
                <div className="relative">
                  <div
                    className="absolute top-1/2 -translate-y-1/2 h-5 rounded shadow-sm"
                    style={{
                      left: `${left}%`,
                      width: `${width}%`,
                      background: RAG_BAR[ln.overall_rag] || "#8A8A8A",
                      opacity: 0.85,
                    }}
                    title={`${ln.reg_approval_date} → ${ln.target_launch_date}`}
                  />
                  {launchGates.map((g) => {
                    const x = (differenceInDays(parseISO(g.target_date!), startDate) / days) * 100;
                    return (
                      <div
                        key={g.id}
                        className="absolute top-1/2 -translate-y-1/2 text-primary text-sm"
                        style={{ left: `${x}%`, transform: "translate(-50%, -50%)" }}
                        title={`${g.name} · ${g.target_date}`}
                      >
                        ★
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
