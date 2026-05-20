import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Select } from "./ui/select";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "./ui/dialog";

interface BudgetLine {
  category: string;
  planned: number;
  actual: number;
  remaining: number;
  utilization_pct: number | null;
  currency: string;
  notes: string | null;
}

interface BudgetResp {
  launch_id: string;
  currency: string;
  lines: BudgetLine[];
  totals: { planned: number; actual: number; remaining: number; utilization_pct: number };
  pnl: {
    y1_revenue_forecast: number;
    y1_opex_planned: number;
    y1_gross_margin_pct: number | null;
    actual_to_date: number;
  };
  available_categories: string[];
}

function fmt(n: number, ccy: string) {
  if (Math.abs(n) >= 1e9) return `${(n / 1e9).toFixed(1)}B ${ccy}`;
  if (Math.abs(n) >= 1e6) return `${(n / 1e6).toFixed(1)}M ${ccy}`;
  if (Math.abs(n) >= 1e3) return `${(n / 1e3).toFixed(1)}k ${ccy}`;
  return `${n.toLocaleString()} ${ccy}`;
}

export function BudgetTab({ launchId }: { launchId: string }) {
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["budget", launchId],
    queryFn: () => api<BudgetResp>(`/launches/${launchId}/budget`),
  });
  const [open, setOpen] = useState<"plan" | "spend" | null>(null);

  if (!data) return <div className="text-mute">Loading budget…</div>;

  const utilColor = (u: number | null) => u === null ? "text-mute" : u > 100 ? "text-destructive" : u > 80 ? "text-[#B8740A]" : "text-mute-2";

  return (
    <div className="space-y-6">
      {/* P&L summary */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="font-mono text-[10px] uppercase tracking-widest text-mute">Y1 revenue forecast</div>
          <div className="font-display text-2xl tracking-tight mt-1">{fmt(data.pnl.y1_revenue_forecast, data.currency)}</div>
        </Card>
        <Card className="p-4">
          <div className="font-mono text-[10px] uppercase tracking-widest text-mute">Y1 OPEX planned</div>
          <div className="font-display text-2xl tracking-tight mt-1">{fmt(data.pnl.y1_opex_planned, data.currency)}</div>
        </Card>
        <Card className="p-4">
          <div className="font-mono text-[10px] uppercase tracking-widest text-mute">Actual to date</div>
          <div className="font-display text-2xl tracking-tight mt-1">{fmt(data.pnl.actual_to_date, data.currency)}</div>
          <div className="text-xs text-mute-2 mt-1">{data.totals.utilization_pct}% of plan</div>
        </Card>
        <Card className={`p-4 ${(data.pnl.y1_gross_margin_pct ?? 0) < 50 ? "border-[#B8740A]/30 bg-[#FAF1E0]" : "border-[#2F7D4F]/30 bg-[#EDF5EF]"}`}>
          <div className="font-mono text-[10px] uppercase tracking-widest text-mute">Y1 gross margin</div>
          <div className="font-display text-2xl tracking-tight mt-1">
            {data.pnl.y1_gross_margin_pct !== null ? `${data.pnl.y1_gross_margin_pct}%` : "—"}
          </div>
        </Card>
      </div>

      {/* Budget lines table */}
      <Card className="p-0 overflow-hidden">
        <div className="px-5 py-3 border-b border-line flex items-center justify-between">
          <h3 className="font-display text-lg tracking-tight">OPEX by category</h3>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setOpen("spend")}>+ Record spend</Button>
            <Button size="sm" onClick={() => setOpen("plan")}>+ Add / update plan</Button>
          </div>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-paper-2 border-b border-line text-left">
            <tr>
              <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Category</th>
              <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute text-right">Planned</th>
              <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute text-right">Actual</th>
              <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute text-right">Remaining</th>
              <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute text-right">Util %</th>
              <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Notes</th>
            </tr>
          </thead>
          <tbody>
            {data.lines.length === 0 && (
              <tr><td colSpan={6} className="p-4 text-mute text-sm">No budget lines yet. Click "Add / update plan" to start.</td></tr>
            )}
            {data.lines.map((l) => (
              <tr key={l.category} className="border-b border-line last:border-0">
                <td className="p-3 font-medium">{l.category}</td>
                <td className="p-3 text-right font-mono">{fmt(l.planned, l.currency)}</td>
                <td className="p-3 text-right font-mono">{fmt(l.actual, l.currency)}</td>
                <td className={`p-3 text-right font-mono ${l.remaining < 0 ? "text-destructive" : ""}`}>{fmt(l.remaining, l.currency)}</td>
                <td className={`p-3 text-right font-mono ${utilColor(l.utilization_pct)}`}>
                  {l.utilization_pct === null ? "—" : `${l.utilization_pct}%`}
                </td>
                <td className="p-3 text-xs text-mute-2">{l.notes ?? ""}</td>
              </tr>
            ))}
            {data.lines.length > 0 && (
              <tr className="bg-paper-2 font-medium">
                <td className="p-3">Total</td>
                <td className="p-3 text-right font-mono">{fmt(data.totals.planned, data.currency)}</td>
                <td className="p-3 text-right font-mono">{fmt(data.totals.actual, data.currency)}</td>
                <td className="p-3 text-right font-mono">{fmt(data.totals.remaining, data.currency)}</td>
                <td className="p-3 text-right font-mono">{data.totals.utilization_pct}%</td>
                <td />
              </tr>
            )}
          </tbody>
        </table>
      </Card>

      {open === "plan" && (
        <PlanModal
          launchId={launchId}
          categories={data.available_categories}
          onClose={() => setOpen(null)}
          onSaved={() => { qc.invalidateQueries({ queryKey: ["budget", launchId] }); setOpen(null); }}
        />
      )}
      {open === "spend" && (
        <SpendModal
          launchId={launchId}
          categories={[...new Set([...data.available_categories, ...data.lines.map((l) => l.category)])]}
          onClose={() => setOpen(null)}
          onSaved={() => { qc.invalidateQueries({ queryKey: ["budget", launchId] }); setOpen(null); }}
        />
      )}
    </div>
  );
}

function PlanModal({ launchId, categories, onClose, onSaved }: { launchId: string; categories: string[]; onClose: () => void; onSaved: () => void }) {
  const [category, setCategory] = useState(categories[0] ?? "");
  const [amount, setAmount] = useState("");
  const [notes, setNotes] = useState("");
  const save = useMutation({
    mutationFn: () =>
      api(`/launches/${launchId}/budget`, {
        method: "POST",
        body: JSON.stringify({ category, planned_amount: Number(amount), notes: notes || undefined }),
      }),
    onSuccess: onSaved,
  });
  return (
    <Dialog open onClose={onClose}>
      <DialogHeader><DialogTitle>Set planned budget</DialogTitle></DialogHeader>
      <DialogContent>
        <div className="space-y-3">
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Category</label>
            <Select value={category} onChange={(e) => setCategory(e.target.value)}>
              {categories.map((c) => <option key={c}>{c}</option>)}
            </Select>
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Planned amount</label>
            <Input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="e.g. 12000000" />
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Notes (optional)</label>
            <Input value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
        </div>
      </DialogContent>
      <DialogFooter>
        <Button variant="outline" onClick={onClose}>Cancel</Button>
        <Button onClick={() => save.mutate()} disabled={!amount || save.isPending}>
          {save.isPending ? "Saving…" : "Save"}
        </Button>
      </DialogFooter>
    </Dialog>
  );
}

function SpendModal({ launchId, categories, onClose, onSaved }: { launchId: string; categories: string[]; onClose: () => void; onSaved: () => void }) {
  const today = new Date().toISOString().slice(0, 7);
  const [category, setCategory] = useState(categories[0] ?? "");
  const [period, setPeriod] = useState(today);
  const [amount, setAmount] = useState("");
  const save = useMutation({
    mutationFn: () =>
      api(`/launches/${launchId}/spend`, {
        method: "POST",
        body: JSON.stringify({ category, period, actual_amount: Number(amount) }),
      }),
    onSuccess: onSaved,
  });
  return (
    <Dialog open onClose={onClose}>
      <DialogHeader><DialogTitle>Record spend</DialogTitle></DialogHeader>
      <DialogContent>
        <div className="space-y-3">
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Category</label>
            <Select value={category} onChange={(e) => setCategory(e.target.value)}>
              {categories.map((c) => <option key={c}>{c}</option>)}
            </Select>
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Period (YYYY-MM)</label>
            <Input type="month" value={period} onChange={(e) => setPeriod(e.target.value)} />
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Actual amount</label>
            <Input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} />
          </div>
        </div>
      </DialogContent>
      <DialogFooter>
        <Button variant="outline" onClick={onClose}>Cancel</Button>
        <Button onClick={() => save.mutate()} disabled={!amount || save.isPending}>
          {save.isPending ? "Saving…" : "Record"}
        </Button>
      </DialogFooter>
    </Dialog>
  );
}
