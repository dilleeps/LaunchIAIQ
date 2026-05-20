import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, RefreshCw, Settings as SettingsIcon, Trash2 } from "lucide-react";
import { api } from "../lib/api";
import { CATEGORY_LABEL, CONNECTOR_SCHEMAS, getSchema, type ConnectorSchema } from "../lib/connectors";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { ConnectorForm } from "../components/ConnectorForm";
import { PageHeader } from "../components/PageHeader";

interface ConnInfo {
  id: string;
  kind: string;
  enabled: boolean;
  last_sync_at?: string | null;
  last_sync_status?: string | null;
  config?: Record<string, any>;
}

interface Available {
  kind: string;
  label: string;
  phase: number;
  auth: string;
}

export function Settings() {
  const qc = useQueryClient();
  const [openSchema, setOpenSchema] = useState<ConnectorSchema | null>(null);
  const [editing, setEditing] = useState<{ schema: ConnectorSchema; conn: ConnInfo } | null>(null);

  const { data: conns } = useQuery({ queryKey: ["conns"], queryFn: () => api<ConnInfo[]>("/integrations") });
  const { data: available } = useQuery({ queryKey: ["conns-available"], queryFn: () => api<Available[]>("/integrations/available") });

  const create = useMutation({
    mutationFn: (vars: { kind: string; config: Record<string, any> }) =>
      api(`/integrations?kind=${encodeURIComponent(vars.kind)}`, {
        method: "POST",
        body: JSON.stringify(vars.config),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["conns"] });
      setOpenSchema(null);
    },
  });
  const sync = useMutation({
    mutationFn: (id: string) => api(`/integrations/${id}/sync`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["conns"] }),
  });

  const grouped = (available || []).reduce<Record<string, Available[]>>((acc, a) => {
    const schema = getSchema(a.kind);
    const cat = schema?.category ?? "market_intel";
    (acc[cat] = acc[cat] || []).push(a);
    return acc;
  }, {});

  return (
    <>
      <PageHeader
        eyebrow="Settings · Integrations"
        title="Connect every system."
        subtitle="Configure CRMs, ERPs, regulatory platforms, identity providers and free market-intelligence feeds. All settings encrypted at rest; sync schedules run nightly."
      />
      <div className="px-10 py-8 space-y-10">
        <section>
          <h2 className="font-mono text-[11px] uppercase tracking-widest text-mute mb-3">Configured</h2>
          {conns?.length === 0 ? (
            <Card className="p-6 text-mute">No connectors yet. Add one below.</Card>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {conns?.map((c) => {
                const meta = available?.find((a) => a.kind === c.kind);
                const schema = getSchema(c.kind);
                // Derive a human-readable target so duplicates are distinguishable
                const target =
                  c.config?.asset_query ||
                  c.config?.query ||
                  c.config?.manufacturer ||
                  c.config?.indicator ||
                  c.config?.label ||
                  "all (no filter)";
                return (
                  <Card key={c.id} className="p-5">
                    <div className="flex items-start justify-between mb-2">
                      <div className="min-w-0">
                        <div className="font-medium">{meta?.label ?? c.kind}</div>
                        <div className="text-xs text-mute font-mono mt-0.5 truncate">
                          {c.kind} · monitors <b className="text-ink-2">{target}</b>
                        </div>
                      </div>
                      <span className="chip rag-Green shrink-0 ml-2">enabled</span>
                    </div>
                    <div className="text-xs text-mute-2 mt-3 grid grid-cols-2 gap-y-1">
                      <span className="text-mute">Last sync</span>
                      <span className="font-mono">{c.last_sync_at ? new Date(c.last_sync_at).toLocaleString() : "never"}</span>
                      <span className="text-mute">Status</span>
                      <span className="font-mono">{c.last_sync_status ?? "—"}</span>
                    </div>
                    <div className="mt-4 flex gap-2">
                      <Button size="sm" onClick={() => sync.mutate(c.id)} disabled={sync.isPending && sync.variables === c.id}>
                        <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                        {sync.isPending && sync.variables === c.id ? "Syncing…" : "Sync now"}
                      </Button>
                      {schema && (
                        <Button size="sm" variant="outline" onClick={() => setEditing({ schema, conn: c })}>
                          <SettingsIcon className="w-3.5 h-3.5 mr-1.5" />
                          Configure
                        </Button>
                      )}
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </section>

        {Object.entries(grouped).map(([category, items]) => (
          <section key={category}>
            <h2 className="font-mono text-[11px] uppercase tracking-widest text-mute mb-3">
              {CATEGORY_LABEL[category as keyof typeof CATEGORY_LABEL]}
            </h2>
            <div className="grid grid-cols-2 gap-3">
              {items.map((a) => {
                const schema = getSchema(a.kind);
                const configured = conns?.some((c) => c.kind === a.kind);
                return (
                  <Card key={a.kind} className="p-5 flex flex-col">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <div className="font-medium">{a.label}</div>
                        <div className="text-xs text-mute font-mono mt-0.5">auth: {a.auth} · Phase {a.phase}</div>
                      </div>
                      {configured && <span className="chip rag-Green">configured</span>}
                    </div>
                    {schema && <p className="text-xs text-mute-2 mt-2 flex-1">{schema.description}</p>}
                    <div className="mt-4">
                      <Button
                        size="sm"
                        variant={configured ? "outline" : "default"}
                        onClick={() => schema && setOpenSchema(schema)}
                        disabled={!schema}
                      >
                        <Plus className="w-3.5 h-3.5 mr-1.5" />
                        {configured ? "Add another" : "Configure"}
                      </Button>
                    </div>
                  </Card>
                );
              })}
            </div>
          </section>
        ))}
      </div>

      <Dialog open={!!openSchema} onClose={() => setOpenSchema(null)}>
        {openSchema && (
          <>
            <DialogHeader>
              <DialogTitle>Configure {openSchema.kind}</DialogTitle>
              <p className="text-sm text-mute-2 mt-1">{openSchema.description}</p>
            </DialogHeader>
            <DialogContent>
              <ConnectorForm
                schema={openSchema}
                submitting={create.isPending}
                onCancel={() => setOpenSchema(null)}
                onSubmit={(values) => create.mutate({ kind: openSchema.kind, config: values })}
              />
            </DialogContent>
          </>
        )}
      </Dialog>

      <Dialog open={!!editing} onClose={() => setEditing(null)}>
        {editing && (
          <>
            <DialogHeader>
              <DialogTitle>Edit {editing.schema.kind}</DialogTitle>
            </DialogHeader>
            <DialogContent>
              <ConnectorForm
                schema={editing.schema}
                initial={editing.conn.config}
                onCancel={() => setEditing(null)}
                onSubmit={() => setEditing(null)}
              />
              <p className="text-xs text-mute mt-3">Editing existing connector config will land in Phase 2; this dialog previews the form.</p>
            </DialogContent>
          </>
        )}
      </Dialog>
    </>
  );
}
