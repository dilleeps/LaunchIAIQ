import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Select } from "./ui/select";
import type { Asset, Country } from "../lib/types";

interface TemplateSummary {
  key: string;
  name: string;
  scope: string;
  regulator_hint: string;
  summary: string;
  group_count: number;
  activity_count: number;
  meeting_count: number;
}

interface TeamMember {
  full_name: string;
  email?: string;
  role_label: string;
  is_manager: boolean;
  country_code?: string;
}

const DEFAULT_TEAM_ROLES = [
  "Country Launch Leader", "Global Brand Lead", "Market Access Lead",
  "Medical Affairs Lead", "Regulatory Lead", "Commercial Lead",
  "Supply Lead", "Patient Services", "MSL", "Field Force Lead",
];

const ASSUMPTION_FIELDS: { key: string; label: string }[] = [
  { key: "commercial_launch_date", label: "Commercial Launch Date" },
  { key: "regulatory_submission", label: "Regulatory Submission" },
  { key: "regulatory_approval", label: "Regulatory Approval" },
  { key: "pricing_submission", label: "Pricing Submission" },
  { key: "pricing_approval", label: "Pricing Approval" },
  { key: "reimbursement_submission", label: "Reimbursement Submission" },
  { key: "reimbursement_approval", label: "Reimbursement Approval" },
  { key: "trade_stock_available", label: "Trade Stock Available By" },
  { key: "phase3_results", label: "Phase 3 Results" },
];

export function NewLaunchWizard({ onClose }: { onClose: () => void }) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [step, setStep] = useState(1);

  // Step 1
  const [templateKey, setTemplateKey] = useState("global_launch_framework_v8");
  const [launchCode, setLaunchCode] = useState("");
  const [assetId, setAssetId] = useState("");
  const [countryId, setCountryId] = useState("");
  const [franchise, setFranchise] = useState("");
  const [brand, setBrand] = useState("");
  const [indicationLabel, setIndicationLabel] = useState("");
  const [region, setRegion] = useState("");
  const [businessPartner, setBusinessPartner] = useState("");

  // Step 2
  const [assumptions, setAssumptions] = useState<Record<string, string>>({});
  const [na, setNa] = useState<Set<string>>(new Set());
  const [pending, setPending] = useState<Set<string>>(new Set());
  const [mrpValue, setMrpValue] = useState("");
  const [mrpCurrency, setMrpCurrency] = useState("USD");
  const [mrpYear, setMrpYear] = useState("");
  const [cumulativeMrp, setCumulativeMrp] = useState("");

  // Step 3 - meetings
  const [ccftDay, setCcftDay] = useState(15);
  const [gps1Off, setGps1Off] = useState(24);
  const [gps2Off, setGps2Off] = useState(18);
  const [gps3Off, setGps3Off] = useState(12);
  const [gps4Off, setGps4Off] = useState(6);
  const [lawOff, setLawOff] = useState(9);
  const [checkpointOff, setCheckpointOff] = useState(18);

  // Step 4 - team
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [tmName, setTmName] = useState("");
  const [tmRole, setTmRole] = useState(DEFAULT_TEAM_ROLES[0]);
  const [tmEmail, setTmEmail] = useState("");
  const [tmManager, setTmManager] = useState(false);

  const { data: templates } = useQuery({
    queryKey: ["launch-templates"],
    queryFn: () => api<TemplateSummary[]>("/launch-templates"),
  });
  const { data: assets } = useQuery({ queryKey: ["assets"], queryFn: () => api<Asset[]>("/assets") });
  const { data: countries } = useQuery({ queryKey: ["countries"], queryFn: () => api<Country[]>("/lookups/countries") });

  const create = useMutation({
    mutationFn: () =>
      api<{ launch_id: string; launch_code: string }>("/launches/wizard", {
        method: "POST",
        body: JSON.stringify({
          launch_code: launchCode,
          template_key: templateKey,
          asset_id: assetId,
          country_id: countryId,
          franchise: franchise || undefined,
          brand: brand || undefined,
          indication_label: indicationLabel || undefined,
          region: region || undefined,
          business_partner: businessPartner || undefined,
          assumptions: {
            ...Object.fromEntries(Object.entries(assumptions).filter(([_, v]) => v)),
            mrp_value: mrpValue ? Number(mrpValue) : undefined,
            mrp_currency: mrpCurrency,
            mrp_year: mrpYear ? Number(mrpYear) : undefined,
            cumulative_mrp: cumulativeMrp ? Number(cumulativeMrp) : undefined,
            not_applicable: Array.from(na),
            pending_confirmation: Array.from(pending),
          },
          meetings: [
            { meeting_key: "ccft", name: "CCFT (Country Cross-Functional Team)", cadence: "monthly", day_of_month: ccftDay, recurring: true },
            { meeting_key: "checkpoint", name: "Country Checkpoint Review L-18M", cadence: "milestone", offset_months_before_launch: checkpointOff, recurring: false },
            { meeting_key: "gps1", name: "GPS Checkpoint Review 1", cadence: "milestone", offset_months_before_launch: gps1Off, recurring: false },
            { meeting_key: "gps2", name: "GPS Checkpoint Review 2", cadence: "milestone", offset_months_before_launch: gps2Off, recurring: false },
            { meeting_key: "gps3", name: "GPS Checkpoint Review 3", cadence: "milestone", offset_months_before_launch: gps3Off, recurring: false },
            { meeting_key: "gps4", name: "GPS Checkpoint Review 4", cadence: "milestone", offset_months_before_launch: gps4Off, recurring: false },
            { meeting_key: "law", name: "Launch Activation Workshop (LAW)", cadence: "milestone", offset_months_before_launch: lawOff, recurring: false },
          ],
          team_members: team,
        }),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["launches"] });
      qc.invalidateQueries({ queryKey: ["overview"] });
      onClose();
      navigate(`/launches/${data.launch_id}`);
    },
  });

  const selectedTemplate = templates?.find((t) => t.key === templateKey);
  const canNext1 = launchCode && assetId && countryId && templateKey;

  const addMember = () => {
    if (!tmName.trim()) return;
    setTeam((prev) => [...prev, { full_name: tmName.trim(), email: tmEmail || undefined, role_label: tmRole, is_manager: tmManager }]);
    setTmName(""); setTmEmail(""); setTmManager(false);
  };

  return (
    <Dialog open onClose={onClose}>
      <div className="w-full max-w-3xl">
        <DialogHeader>
          <DialogTitle>Create New Launch</DialogTitle>
          <div className="mt-3 flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-mute">
            {[
              { n: 1, label: "Template & Identity" },
              { n: 2, label: "Key Launch Assumptions" },
              { n: 3, label: "Launch Management Meetings" },
              { n: 4, label: "Team Members" },
            ].map((s) => (
              <button
                key={s.n}
                onClick={() => setStep(s.n)}
                className={`px-3 py-1.5 rounded ${step === s.n ? "bg-primary text-paper" : step > s.n ? "bg-primary-soft text-primary" : "bg-paper-2 text-mute"}`}
              >
                {s.n}. {s.label}
              </button>
            ))}
          </div>
        </DialogHeader>

        <DialogContent>
          {step === 1 && (
            <div className="space-y-4">
              <FieldLabel>Launch Template</FieldLabel>
              <Select value={templateKey} onChange={(e) => setTemplateKey(e.target.value)}>
                {templates?.map((t) => (
                  <option key={t.key} value={t.key}>
                    {t.name} — {t.scope}
                  </option>
                ))}
              </Select>
              {selectedTemplate && (
                <div className="text-xs text-mute-2 bg-paper-2 p-3 rounded border border-line">
                  <div className="mb-1">{selectedTemplate.summary}</div>
                  <div className="font-mono text-[10px] uppercase tracking-wider text-mute">
                    {selectedTemplate.regulator_hint} · {selectedTemplate.group_count} groups · {selectedTemplate.activity_count} activities · {selectedTemplate.meeting_count} meetings
                  </div>
                </div>
              )}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <FieldLabel>Launch Code *</FieldLabel>
                  <Input value={launchCode} onChange={(e) => setLaunchCode(e.target.value)} placeholder="e.g. L-200" />
                </div>
                <div>
                  <FieldLabel>Franchise</FieldLabel>
                  <Input value={franchise} onChange={(e) => setFranchise(e.target.value)} placeholder="e.g. Neuroscience" />
                </div>
                <div>
                  <FieldLabel>Brand / Asset *</FieldLabel>
                  <Select value={assetId} onChange={(e) => setAssetId(e.target.value)}>
                    <option value="">— Select brand —</option>
                    {assets?.map((a) => <option key={a.id} value={a.id}>{a.brand_name}</option>)}
                  </Select>
                </div>
                <div>
                  <FieldLabel>Indication</FieldLabel>
                  <Input value={indicationLabel} onChange={(e) => setIndicationLabel(e.target.value)} placeholder="e.g. Plaque Psoriasis (PsO)" />
                </div>
                <div>
                  <FieldLabel>Country *</FieldLabel>
                  <Select value={countryId} onChange={(e) => setCountryId(e.target.value)}>
                    <option value="">— Select country —</option>
                    {countries?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </Select>
                </div>
                <div>
                  <FieldLabel>Region / Business Partner</FieldLabel>
                  <Input value={businessPartner} onChange={(e) => setBusinessPartner(e.target.value)} placeholder="e.g. EUCAN, GEM" />
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div className="bg-paper-2 p-3 rounded border border-line">
                <div className="font-mono text-[10px] uppercase tracking-widest text-mute mb-2">Maximum Revenue Potential (MRP)</div>
                <div className="grid grid-cols-4 gap-2">
                  <div>
                    <FieldLabel>Cumulative MRP</FieldLabel>
                    <Input type="number" value={cumulativeMrp} onChange={(e) => setCumulativeMrp(e.target.value)} placeholder="1200000000" />
                  </div>
                  <div>
                    <FieldLabel>Peak MRP</FieldLabel>
                    <Input type="number" value={mrpValue} onChange={(e) => setMrpValue(e.target.value)} placeholder="250000000" />
                  </div>
                  <div>
                    <FieldLabel>Currency</FieldLabel>
                    <Select value={mrpCurrency} onChange={(e) => setMrpCurrency(e.target.value)}>
                      {["USD", "EUR", "JPY", "GBP", "CHF"].map((c) => <option key={c}>{c}</option>)}
                    </Select>
                  </div>
                  <div>
                    <FieldLabel>MRP Year</FieldLabel>
                    <Input type="number" value={mrpYear} onChange={(e) => setMrpYear(e.target.value)} placeholder="2032" />
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="font-mono text-[10px] uppercase tracking-widest text-mute">Key Dates</div>
                {ASSUMPTION_FIELDS.map((f) => (
                  <div key={f.key} className="grid grid-cols-12 gap-2 items-center">
                    <div className="col-span-4 text-sm">{f.label}</div>
                    <Input
                      type="date"
                      className="col-span-4"
                      disabled={na.has(f.key)}
                      value={assumptions[f.key] || ""}
                      onChange={(e) => setAssumptions((prev) => ({ ...prev, [f.key]: e.target.value }))}
                    />
                    <label className="col-span-2 flex items-center gap-1 text-xs text-mute-2">
                      <input
                        type="checkbox"
                        checked={na.has(f.key)}
                        onChange={(e) => setNa((prev) => {
                          const next = new Set(prev);
                          e.target.checked ? next.add(f.key) : next.delete(f.key);
                          return next;
                        })}
                      />
                      N/A
                    </label>
                    <label className="col-span-2 flex items-center gap-1 text-xs text-mute-2">
                      <input
                        type="checkbox"
                        checked={pending.has(f.key)}
                        onChange={(e) => setPending((prev) => {
                          const next = new Set(prev);
                          e.target.checked ? next.add(f.key) : next.delete(f.key);
                          return next;
                        })}
                      />
                      Pending
                    </label>
                  </div>
                ))}
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-3">
              <div className="text-xs text-mute-2">
                Default cadence for Launch Management Meetings. CCFT recurs monthly; others are scheduled relative to commercial launch.
              </div>
              <MeetingRow label="CCFT (monthly)" hint="Day of month" value={ccftDay} onChange={setCcftDay} unit="day" />
              <MeetingRow label="Country Checkpoint Review" hint="L-month before launch" value={checkpointOff} onChange={setCheckpointOff} unit="months before" />
              <MeetingRow label="GPS Checkpoint Review 1" hint="Months before launch" value={gps1Off} onChange={setGps1Off} unit="months before" />
              <MeetingRow label="GPS Checkpoint Review 2" hint="Months before launch" value={gps2Off} onChange={setGps2Off} unit="months before" />
              <MeetingRow label="GPS Checkpoint Review 3" hint="Months before launch" value={gps3Off} onChange={setGps3Off} unit="months before" />
              <MeetingRow label="GPS Checkpoint Review 4" hint="Months before launch" value={gps4Off} onChange={setGps4Off} unit="months before" />
              <MeetingRow label="Launch Activation Workshop (LAW)" hint="Months before launch" value={lawOff} onChange={setLawOff} unit="months before" />
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              <div className="grid grid-cols-12 gap-2 items-end">
                <div className="col-span-4">
                  <FieldLabel>Full Name</FieldLabel>
                  <Input value={tmName} onChange={(e) => setTmName(e.target.value)} placeholder="e.g. Kato Koki" />
                </div>
                <div className="col-span-4">
                  <FieldLabel>Role</FieldLabel>
                  <Select value={tmRole} onChange={(e) => setTmRole(e.target.value)}>
                    {DEFAULT_TEAM_ROLES.map((r) => <option key={r}>{r}</option>)}
                  </Select>
                </div>
                <div className="col-span-3">
                  <FieldLabel>Email</FieldLabel>
                  <Input value={tmEmail} onChange={(e) => setTmEmail(e.target.value)} placeholder="optional" />
                </div>
                <div className="col-span-1 flex justify-center pb-2">
                  <label className="flex items-center gap-1 text-xs">
                    <input type="checkbox" checked={tmManager} onChange={(e) => setTmManager(e.target.checked)} />
                    Mgr
                  </label>
                </div>
                <Button size="sm" className="col-span-12 w-fit" onClick={addMember}>+ Add member</Button>
              </div>

              <div className="border border-line rounded overflow-hidden">
                <div className="bg-paper-2 px-3 py-2 font-mono text-[10px] uppercase tracking-widest text-mute">
                  Team ({team.length})
                </div>
                {team.length === 0 && <div className="p-4 text-mute text-sm">No team members yet.</div>}
                {team.map((m, i) => (
                  <div key={i} className="px-3 py-2 border-t border-line flex items-center justify-between text-sm">
                    <div>
                      <span className="font-medium">{m.full_name}</span>
                      {m.is_manager && <span className="ml-2 text-[10px] font-mono uppercase tracking-wider text-primary">Manager</span>}
                      <div className="text-xs text-mute-2">{m.role_label}{m.email ? ` · ${m.email}` : ""}</div>
                    </div>
                    <button
                      onClick={() => setTeam((prev) => prev.filter((_, j) => j !== i))}
                      className="text-xs text-destructive hover:underline"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </DialogContent>

        <DialogFooter>
          {step > 1 && <Button variant="outline" onClick={() => setStep(step - 1)}>Back</Button>}
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          {step < 4 && (
            <Button onClick={() => setStep(step + 1)} disabled={step === 1 && !canNext1}>Next</Button>
          )}
          {step === 4 && (
            <Button onClick={() => create.mutate()} disabled={create.isPending || !canNext1}>
              {create.isPending ? "Creating…" : "Create Launch"}
            </Button>
          )}
        </DialogFooter>
        {create.isError && <div className="px-6 pb-4 text-xs text-destructive">{String((create.error as Error).message)}</div>}
      </div>
    </Dialog>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <div className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">{children}</div>;
}

function MeetingRow({ label, hint, value, onChange, unit }: { label: string; hint: string; value: number; onChange: (n: number) => void; unit: string }) {
  return (
    <div className="grid grid-cols-12 gap-2 items-center border border-line rounded p-2.5">
      <div className="col-span-6">
        <div className="text-sm font-medium">{label}</div>
        <div className="text-[10px] text-mute font-mono uppercase tracking-wider">{hint}</div>
      </div>
      <div className="col-span-3">
        <Input type="number" value={value} onChange={(e) => onChange(Number(e.target.value) || 0)} />
      </div>
      <div className="col-span-3 text-xs text-mute-2">{unit}</div>
    </div>
  );
}
