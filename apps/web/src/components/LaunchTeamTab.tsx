import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card } from "./ui/card";
import { Input } from "./ui/input";
import { Select } from "./ui/select";
import { Button } from "./ui/button";

interface TeamMember {
  id: string;
  launch_id: string;
  user_id?: string | null;
  full_name?: string | null;
  email?: string | null;
  role_label: string;
  country_code?: string | null;
  is_manager: boolean;
  therapy_area?: string | null;
}

interface Meeting {
  id: string;
  launch_id: string;
  meeting_key: string;
  name: string;
  cadence: string;
  day_of_month?: number | null;
  offset_months_before_launch?: number | null;
  scheduled_date?: string | null;
  recurring: boolean;
  notes?: string | null;
}

const ROLES = [
  "Country Launch Leader", "Global Brand Lead", "Market Access Lead",
  "Medical Affairs Lead", "Regulatory Lead", "Commercial Lead",
  "Supply Lead", "Patient Services", "MSL", "Field Force Lead",
  "HTA Lead", "Pricing Lead", "Forecasting", "Manager", "Other",
];

export function LaunchTeamTab({ launchId, countryCode }: { launchId: string; countryCode?: string }) {
  const qc = useQueryClient();
  const { data: team } = useQuery({
    queryKey: ["launch-team", launchId],
    queryFn: () => api<TeamMember[]>(`/launches/${launchId}/team`),
  });
  const { data: meetings } = useQuery({
    queryKey: ["launch-meetings", launchId],
    queryFn: () => api<Meeting[]>(`/launches/${launchId}/meetings`),
  });

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState(ROLES[0]);
  const [isMgr, setIsMgr] = useState(false);

  const add = useMutation({
    mutationFn: () =>
      api(`/launches/${launchId}/team`, {
        method: "POST",
        body: JSON.stringify({ full_name: name, email: email || undefined, role_label: role, is_manager: isMgr, country_code: countryCode }),
      }),
    onSuccess: () => {
      setName(""); setEmail(""); setIsMgr(false);
      qc.invalidateQueries({ queryKey: ["launch-team", launchId] });
    },
  });

  const remove = useMutation({
    mutationFn: (id: string) => api(`/launches/${launchId}/team/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["launch-team", launchId] }),
  });

  return (
    <div className="space-y-6">
      <Card className="p-0 overflow-hidden">
        <div className="px-5 py-3 border-b border-line">
          <h3 className="font-display text-lg tracking-tight">Launch Team ({team?.length ?? 0})</h3>
          <p className="text-xs text-mute-2 mt-0.5">People assigned to this launch with their roles.</p>
        </div>
        <div className="p-5 border-b border-line bg-paper-2">
          <div className="grid grid-cols-12 gap-2 items-end">
            <div className="col-span-3">
              <Label>Name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Full name" />
            </div>
            <div className="col-span-3">
              <Label>Role</Label>
              <Select value={role} onChange={(e) => setRole(e.target.value)}>
                {ROLES.map((r) => <option key={r}>{r}</option>)}
              </Select>
            </div>
            <div className="col-span-3">
              <Label>Email</Label>
              <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="optional" />
            </div>
            <div className="col-span-1 flex justify-center pb-2">
              <label className="flex items-center gap-1 text-xs">
                <input type="checkbox" checked={isMgr} onChange={(e) => setIsMgr(e.target.checked)} />
                Mgr
              </label>
            </div>
            <div className="col-span-2">
              <Button size="sm" className="w-full" disabled={!name.trim() || add.isPending} onClick={() => add.mutate()}>
                {add.isPending ? "Adding…" : "+ Add member"}
              </Button>
            </div>
          </div>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-paper-2 border-b border-line">
            <tr className="text-left">
              <th className="p-3 font-mono text-[10px] uppercase tracking-widest text-mute">Name</th>
              <th className="p-3 font-mono text-[10px] uppercase tracking-widest text-mute">Role</th>
              <th className="p-3 font-mono text-[10px] uppercase tracking-widest text-mute">Email</th>
              <th className="p-3 font-mono text-[10px] uppercase tracking-widest text-mute">Country</th>
              <th className="p-3 font-mono text-[10px] uppercase tracking-widest text-mute"></th>
            </tr>
          </thead>
          <tbody>
            {(team || []).map((m) => (
              <tr key={m.id} className="border-b border-line last:border-0">
                <td className="p-3">
                  {m.full_name || "—"}
                  {m.is_manager && <span className="ml-2 text-[10px] font-mono uppercase tracking-wider text-primary">Manager</span>}
                </td>
                <td className="p-3 text-mute-2">{m.role_label}</td>
                <td className="p-3 text-mute-2 text-xs">{m.email || "—"}</td>
                <td className="p-3 text-mute-2 text-xs">{m.country_code || "—"}</td>
                <td className="p-3 text-right">
                  <button onClick={() => remove.mutate(m.id)} className="text-xs text-destructive hover:underline">Remove</button>
                </td>
              </tr>
            ))}
            {(team || []).length === 0 && (
              <tr><td colSpan={5} className="p-6 text-mute text-center">No team members yet.</td></tr>
            )}
          </tbody>
        </table>
      </Card>

      <Card className="p-0 overflow-hidden">
        <div className="px-5 py-3 border-b border-line">
          <h3 className="font-display text-lg tracking-tight">Launch Management Meetings ({meetings?.length ?? 0})</h3>
          <p className="text-xs text-mute-2 mt-0.5">Default cadence configured at launch creation. CCFT recurs monthly; checkpoints scheduled relative to launch.</p>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-paper-2 border-b border-line">
            <tr className="text-left">
              <th className="p-3 font-mono text-[10px] uppercase tracking-widest text-mute">Meeting</th>
              <th className="p-3 font-mono text-[10px] uppercase tracking-widest text-mute">Cadence</th>
              <th className="p-3 font-mono text-[10px] uppercase tracking-widest text-mute">When</th>
              <th className="p-3 font-mono text-[10px] uppercase tracking-widest text-mute">Recurring</th>
            </tr>
          </thead>
          <tbody>
            {(meetings || []).map((m) => (
              <tr key={m.id} className="border-b border-line last:border-0">
                <td className="p-3 font-medium">{m.name}</td>
                <td className="p-3 text-mute-2 text-xs">{m.cadence}</td>
                <td className="p-3 text-mute-2 text-xs">
                  {m.day_of_month ? `Day ${m.day_of_month} of month` :
                   m.offset_months_before_launch ? `L-${m.offset_months_before_launch} months` :
                   m.scheduled_date || "—"}
                </td>
                <td className="p-3 text-xs">{m.recurring ? "Yes" : "No"}</td>
              </tr>
            ))}
            {(meetings || []).length === 0 && (
              <tr><td colSpan={4} className="p-6 text-mute text-center">No meetings configured.</td></tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return <div className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">{children}</div>;
}
