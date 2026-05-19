import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { PageHeader } from "../components/PageHeader";

interface ConnInfo {
  id: string;
  kind: string;
  enabled: boolean;
  last_sync_at?: string | null;
  last_sync_status?: string | null;
}

interface AvailableConn {
  kind: string;
  label: string;
  phase: number;
  auth: string;
}

export function Admin() {
  const qc = useQueryClient();
  const { data: conns } = useQuery({
    queryKey: ["conns"],
    queryFn: () => api<ConnInfo[]>("/integrations"),
  });
  const { data: available } = useQuery({
    queryKey: ["conns-available"],
    queryFn: () => api<AvailableConn[]>("/integrations/available"),
  });
  const sync = useMutation({
    mutationFn: (id: string) => api(`/integrations/${id}/sync`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["conns"] }),
  });

  return (
    <>
      <PageHeader
        eyebrow="Settings · Integrations"
        title="Connectors."
        subtitle="Free market-intelligence sources are wired in Phase 1. Veeva / SAP / SSO connectors land in Phase 2+."
      />
      <div className="px-10 py-8 space-y-10">
        <section>
          <h2 className="font-mono text-[11px] uppercase tracking-widest text-mute mb-3">Configured</h2>
          <div className="border border-line rounded bg-paper overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-paper-2 border-b border-line text-left">
                <tr>
                  <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Kind</th>
                  <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Last sync</th>
                  <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Status</th>
                  <th className="p-3"></th>
                </tr>
              </thead>
              <tbody>
                {conns?.length === 0 && <tr><td colSpan={4} className="p-4 text-mute">No connectors configured yet.</td></tr>}
                {conns?.map((c) => (
                  <tr key={c.id} className="border-b border-line last:border-0">
                    <td className="p-3 font-mono">{c.kind}</td>
                    <td className="p-3 font-mono text-xs">{c.last_sync_at ?? "never"}</td>
                    <td className="p-3 text-mute-2">{c.last_sync_status ?? "—"}</td>
                    <td className="p-3 text-right">
                      <button
                        disabled={sync.isPending}
                        onClick={() => sync.mutate(c.id)}
                        className="px-3 py-1.5 border border-line rounded text-xs font-mono uppercase tracking-wider hover:bg-paper-3"
                      >
                        {sync.isPending && sync.variables === c.id ? "Syncing…" : "Sync now"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section>
          <h2 className="font-mono text-[11px] uppercase tracking-widest text-mute mb-3">Available connectors</h2>
          <div className="grid grid-cols-2 gap-3">
            {available?.map((a) => (
              <div key={a.kind} className="border border-line rounded p-4 bg-paper">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium">{a.label}</span>
                  <span className="chip rag-Pending">Phase {a.phase}</span>
                </div>
                <div className="text-xs text-mute-2 font-mono">{a.kind} · auth: {a.auth}</div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </>
  );
}
