import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api } from "../lib/api";
import type { Launch } from "../lib/types";
import { PageHeader } from "../components/PageHeader";
import { Card } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select } from "../components/ui/select";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "../components/ui/form";

interface Scenario {
  id: string;
  base_launch_id: string;
  name: string;
  parent_scenario_id?: string | null;
  created_at: string;
}

interface IRPResult {
  target_launch_id: string;
  target_launch_code: string;
  current_price: number;
  new_implied_price: number;
  revenue_delta: number;
  currency: string;
}

const scenarioSchema = z.object({
  base_launch_id: z.string().uuid("Pick a launch"),
  name: z.string().min(2, "Name your scenario"),
});

const irpSchema = z.object({
  source_launch_id: z.string().uuid(),
  new_net_price: z.coerce.number().positive("Price must be positive"),
});

export function Scenarios() {
  const qc = useQueryClient();
  const { data: launches } = useQuery({ queryKey: ["launches"], queryFn: () => api<Launch[]>("/launches") });
  const { data: scenarios } = useQuery({ queryKey: ["scenarios"], queryFn: () => api<Scenario[]>("/scenarios") });

  const create = useMutation({
    mutationFn: (v: z.infer<typeof scenarioSchema>) =>
      api("/scenarios", { method: "POST", body: JSON.stringify(v) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scenarios"] }),
  });

  const [irpResult, setIrpResult] = useState<IRPResult[] | null>(null);
  const irpMutation = useMutation({
    mutationFn: (v: z.infer<typeof irpSchema>) =>
      api<IRPResult[]>("/irp/simulate", { method: "POST", body: JSON.stringify(v) }),
    onSuccess: (data) => setIrpResult(data),
  });

  const scenarioForm = useForm<z.infer<typeof scenarioSchema>>({
    resolver: zodResolver(scenarioSchema) as any,
    defaultValues: { base_launch_id: "", name: "" },
  });
  const irpForm = useForm<z.infer<typeof irpSchema>>({
    resolver: zodResolver(irpSchema) as any,
    defaultValues: { source_launch_id: "", new_net_price: 0 },
  });

  return (
    <>
      <PageHeader
        eyebrow="What-if planning"
        title="Scenarios & price cascades."
        subtitle="Clone a launch plan to model alternatives without touching the baseline. Run an IRP simulation to see how a price change in one market cascades across reference-pricing-linked countries."
      />
      <div className="px-10 py-8 grid grid-cols-2 gap-8">
        {/* Scenario clone */}
        <section>
          <h2 className="font-mono text-[11px] uppercase tracking-widest text-mute mb-3">Clone a scenario</h2>
          <Card className="p-6">
            <Form {...scenarioForm}>
              <form onSubmit={scenarioForm.handleSubmit((v) => create.mutate(v))} className="space-y-4">
                <FormField
                  control={scenarioForm.control}
                  name="base_launch_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Base launch</FormLabel>
                      <FormControl>
                        <Select {...field}>
                          <option value="">Choose launch…</option>
                          {launches?.map((l) => (
                            <option key={l.id} value={l.id}>
                              {l.launch_code} — {l.asset.brand_name} · {l.country.name}
                            </option>
                          ))}
                        </Select>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={scenarioForm.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Scenario name</FormLabel>
                      <FormControl>
                        <Input placeholder="e.g. Aggressive launch — delay HTA submission" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button type="submit" disabled={create.isPending}>
                  {create.isPending ? "Cloning…" : "Create scenario"}
                </Button>
              </form>
            </Form>
          </Card>

          <h3 className="font-mono text-[11px] uppercase tracking-widest text-mute mt-6 mb-2">Existing scenarios</h3>
          <div className="space-y-2">
            {scenarios?.length === 0 && <p className="text-sm text-mute">No scenarios yet.</p>}
            {scenarios?.map((s) => (
              <Card key={s.id} className="p-4">
                <div className="flex items-center justify-between">
                  <div className="font-medium">{s.name}</div>
                  <span className="text-xs font-mono text-mute">{new Date(s.created_at).toLocaleDateString()}</span>
                </div>
                <div className="text-xs text-mute-2 mt-1 font-mono">base: {s.base_launch_id.slice(0, 8)}…</div>
              </Card>
            ))}
          </div>
        </section>

        {/* IRP simulator */}
        <section>
          <h2 className="font-mono text-[11px] uppercase tracking-widest text-mute mb-3">IRP price cascade simulator</h2>
          <Card className="p-6">
            <Form {...irpForm}>
              <form onSubmit={irpForm.handleSubmit((v) => irpMutation.mutate(v))} className="space-y-4">
                <FormField
                  control={irpForm.control}
                  name="source_launch_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Source launch</FormLabel>
                      <FormControl>
                        <Select {...field}>
                          <option value="">Choose launch…</option>
                          {launches?.map((l) => (
                            <option key={l.id} value={l.id}>
                              {l.launch_code} — {l.asset.brand_name} · {l.country.name}
                            </option>
                          ))}
                        </Select>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={irpForm.control}
                  name="new_net_price"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>New net price (per patient)</FormLabel>
                      <FormControl>
                        <Input type="number" step="any" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button type="submit" disabled={irpMutation.isPending}>
                  {irpMutation.isPending ? "Simulating…" : "Run cascade"}
                </Button>
              </form>
            </Form>
          </Card>

          {irpResult && (
            <div className="mt-6">
              <h3 className="font-mono text-[11px] uppercase tracking-widest text-mute mb-2">Downstream impact</h3>
              {irpResult.length === 0 ? (
                <p className="text-sm text-mute">No reference-pricing links downstream.</p>
              ) : (
                <Card className="overflow-hidden p-0">
                  <table className="w-full text-sm">
                    <thead className="bg-paper-2 border-b border-line text-left">
                      <tr>
                        <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Launch</th>
                        <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Current</th>
                        <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">New implied</th>
                        <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Δ Revenue</th>
                      </tr>
                    </thead>
                    <tbody>
                      {irpResult.map((r) => (
                        <tr key={r.target_launch_id} className="border-b border-line last:border-0">
                          <td className="p-3 font-mono">{r.target_launch_code}</td>
                          <td className="p-3 font-mono text-xs">{r.current_price.toLocaleString()} {r.currency}</td>
                          <td className="p-3 font-mono text-xs">{r.new_implied_price.toLocaleString()} {r.currency}</td>
                          <td className={`p-3 font-mono text-xs ${r.revenue_delta < 0 ? "text-destructive" : "text-primary"}`}>
                            {r.revenue_delta >= 0 ? "+" : ""}{(r.revenue_delta / 1e6).toFixed(1)}M {r.currency}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Card>
              )}
            </div>
          )}
        </section>
      </div>
    </>
  );
}
