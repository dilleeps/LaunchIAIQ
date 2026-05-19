import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { Launch, Milestone } from "../lib/types";
import { PageHeader } from "../components/PageHeader";

export function Milestones() {
  const { data: upcoming } = useQuery({
    queryKey: ["upcoming-milestones"],
    queryFn: () => api<Milestone[]>("/milestones/upcoming?days=90"),
  });
  const { data: launches } = useQuery({
    queryKey: ["launches"],
    queryFn: () => api<Launch[]>("/launches"),
  });

  const launchMap = new Map((launches || []).map((l) => [l.id, l]));

  return (
    <>
      <PageHeader
        eyebrow="Milestone Tracker"
        title="Next 90 days."
        subtitle="Upcoming milestones across all launches, sorted by target date. Gate milestones (★) require sign-off."
      />
      <div className="px-10 py-8">
        <div className="border border-line rounded-lg overflow-hidden bg-paper">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-paper-2 text-left">
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Target</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Launch</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Milestone</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Status</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Weight</th>
              </tr>
            </thead>
            <tbody>
              {upcoming?.map((m) => {
                const ln = launchMap.get(m.launch_id);
                return (
                  <tr key={m.id} className="border-b border-line last:border-0">
                    <td className="p-3 font-mono text-xs">{m.target_date}</td>
                    <td className="p-3">
                      <div className="font-mono text-[11px] text-mute uppercase tracking-wider">{ln?.launch_code}</div>
                      <div>{ln?.asset.brand_name} · {ln?.country.name}</div>
                    </td>
                    <td className="p-3">
                      {m.is_gate && <span className="text-accent mr-1">★</span>}
                      {m.name}
                    </td>
                    <td className="p-3 text-mute-2">{m.status}</td>
                    <td className="p-3 font-mono text-xs">{m.weight}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
