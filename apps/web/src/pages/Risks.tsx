import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { Risk } from "../lib/types";
import { PageHeader } from "../components/PageHeader";
import { Card } from "../components/ui/card";

const SCORE_BADGE = (score: number) =>
  score >= 6 ? "rag-Red" : score >= 4 ? "rag-Amber" : "rag-Green";

export function Risks() {
  const { data } = useQuery({ queryKey: ["all-risks"], queryFn: () => api<Risk[]>("/risks") });
  const total = data?.length ?? 0;
  const open = data?.filter((r) => r.status !== "Closed").length ?? 0;
  const high = data?.filter((r) => r.score >= 6 && r.status !== "Closed").length ?? 0;

  return (
    <>
      <PageHeader
        eyebrow="Portfolio risk register"
        title="What could derail us."
        subtitle="Active risks across all launches, scored by likelihood × impact. Portfolio-scope risks (e.g. shared supply) link to multiple launches."
      />
      <div className="px-10 py-6 grid grid-cols-3 gap-4">
        <StatCard label="Total risks" value={total} />
        <StatCard label="Open" value={open} />
        <StatCard label="High severity" value={high} accent />
      </div>
      <div className="px-10 pb-10 space-y-3">
        {data?.map((r) => (
          <Card key={r.id} className="p-5">
            <div className="flex items-start gap-3">
              <span className={`chip ${SCORE_BADGE(r.score)}`}>Score {r.score}</span>
              <span className="chip rag-Pending">{r.category ?? "Uncategorised"}</span>
              <span className="chip rag-Pending">{r.scope_type}</span>
              <span className="chip rag-Pending">L:{r.likelihood} · I:{r.impact}</span>
              <span className="chip rag-Pending ml-auto">{r.status}</span>
            </div>
            <div className="mt-3 font-medium">{r.description}</div>
            {r.mitigation && (
              <div className="mt-2 text-sm text-mute-2">
                <span className="font-mono text-[10px] uppercase tracking-wider text-mute mr-2">Mitigation</span>
                {r.mitigation}
              </div>
            )}
          </Card>
        ))}
      </div>
    </>
  );
}

function StatCard({ label, value, accent }: { label: string; value: number; accent?: boolean }) {
  return (
    <Card className={`p-5 ${accent ? "border-primary bg-primary-soft" : ""}`}>
      <div className="font-mono text-[10px] uppercase tracking-widest text-mute">{label}</div>
      <div className="font-display text-3xl tracking-tight mt-2">{value}</div>
    </Card>
  );
}
