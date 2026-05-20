import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { Launch, Milestone } from "../lib/types";
import { PageHeader } from "../components/PageHeader";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select } from "../components/ui/select";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { useCapabilities } from "../hooks/useCapabilities";

interface Task {
  id: string;
  milestone_id: string;
  name: string;
  status: string;
  due_date?: string | null;
}

const STATUSES = ["Not Started", "On Track", "At Risk", "Delayed", "Blocked", "Complete"];

export function Milestones() {
  const { can } = useCapabilities();
  const [editing, setEditing] = useState<Milestone | null>(null);

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
        subtitle="Click any row to edit status, dates, owner, and add sub-tasks. Every change is captured in the audit log."
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
                <th />
              </tr>
            </thead>
            <tbody>
              {upcoming?.map((m) => {
                const ln = launchMap.get(m.launch_id);
                return (
                  <tr
                    key={m.id}
                    className="border-b border-line last:border-0 hover:bg-paper-2 cursor-pointer"
                    onClick={() => setEditing(m)}
                  >
                    <td className="p-3 font-mono text-xs">{m.target_date}</td>
                    <td className="p-3">
                      <div className="font-mono text-[11px] text-mute uppercase tracking-wider">{ln?.launch_code}</div>
                      <div>{ln?.asset.brand_name} · {ln?.country.name}</div>
                    </td>
                    <td className="p-3">
                      {m.is_gate && <span className="text-primary mr-1">★</span>}
                      {m.name}
                    </td>
                    <td className="p-3 text-mute-2">
                      <span className={`chip ${m.status === "Complete" ? "rag-Green" : m.status === "At Risk" || m.status === "Blocked" || m.status === "Delayed" ? "rag-Red" : m.status === "On Track" ? "rag-Green" : "rag-Pending"}`}>
                        {m.status}
                      </span>
                    </td>
                    <td className="p-3 font-mono text-xs">{m.weight}</td>
                    <td className="p-3 text-right text-mute font-mono text-[10px]">edit ›</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {editing && (
        <MilestoneEditor
          milestone={editing}
          launch={launchMap.get(editing.launch_id)}
          editable={can("edit_milestone")}
          canTask={can("edit_task")}
          onClose={() => setEditing(null)}
        />
      )}
    </>
  );
}

function MilestoneEditor({
  milestone, launch, editable, canTask, onClose,
}: {
  milestone: Milestone; launch?: Launch; editable: boolean; canTask: boolean; onClose: () => void;
}) {
  const qc = useQueryClient();
  const [status, setStatus] = useState(milestone.status);
  const [targetDate, setTargetDate] = useState(milestone.target_date ?? "");
  const [actualDate, setActualDate] = useState(milestone.actual_date ?? "");
  const [notes, setNotes] = useState(milestone.notes ?? "");

  const save = useMutation({
    mutationFn: () =>
      api(`/milestones/${milestone.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          status,
          target_date: targetDate || null,
          actual_date: actualDate || null,
          notes: notes || null,
        }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["upcoming-milestones"] });
      qc.invalidateQueries({ queryKey: ["ms", milestone.launch_id] });
      qc.invalidateQueries({ queryKey: ["audit"] });
      onClose();
    },
  });

  const tasksQ = useQuery({
    queryKey: ["tasks", milestone.id],
    queryFn: () => api<Task[]>(`/milestones/${milestone.id}/tasks`),
  });

  const [newTask, setNewTask] = useState("");
  const addTask = useMutation({
    mutationFn: () =>
      api(`/milestones/${milestone.id}/tasks`, {
        method: "POST",
        body: JSON.stringify({ name: newTask, status: "Not Started" }),
      }),
    onSuccess: () => {
      setNewTask("");
      qc.invalidateQueries({ queryKey: ["tasks", milestone.id] });
      qc.invalidateQueries({ queryKey: ["audit"] });
    },
  });

  const toggleTask = useMutation({
    mutationFn: (t: Task) =>
      api(`/tasks/${t.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: t.status === "Complete" ? "Not Started" : "Complete" }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks", milestone.id] });
      qc.invalidateQueries({ queryKey: ["audit"] });
    },
  });

  return (
    <Dialog open onClose={onClose}>
      <DialogHeader>
        <DialogTitle>{milestone.is_gate && <span className="text-primary mr-2">★</span>}{milestone.name}</DialogTitle>
        <div className="text-sm text-mute-2 mt-1">
          {launch?.launch_code} · {launch?.asset.brand_name} · {launch?.country.name}
        </div>
      </DialogHeader>
      <DialogContent>
        <div className="space-y-3">
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Status</label>
            <Select value={status} onChange={(e) => setStatus(e.target.value)} disabled={!editable}>
              {STATUSES.map((s) => <option key={s}>{s}</option>)}
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Target date</label>
              <Input type="date" value={targetDate} onChange={(e) => setTargetDate(e.target.value)} disabled={!editable} />
            </div>
            <div>
              <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Actual date</label>
              <Input type="date" value={actualDate} onChange={(e) => setActualDate(e.target.value)} disabled={!editable} />
            </div>
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Notes</label>
            <Input value={notes} onChange={(e) => setNotes(e.target.value)} disabled={!editable} />
          </div>

          <div className="border-t border-line pt-3 mt-4">
            <div className="font-mono text-[11px] uppercase tracking-widest text-mute mb-2">Sub-tasks</div>
            <ul className="space-y-1 mb-2">
              {tasksQ.data?.length === 0 && <li className="text-xs text-mute">No tasks yet.</li>}
              {tasksQ.data?.map((t) => (
                <li key={t.id} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={t.status === "Complete"}
                    disabled={!canTask}
                    onChange={() => toggleTask.mutate(t)}
                  />
                  <span className={t.status === "Complete" ? "line-through text-mute" : ""}>{t.name}</span>
                </li>
              ))}
            </ul>
            {canTask && (
              <div className="flex gap-2">
                <Input
                  placeholder="Add a sub-task…"
                  value={newTask}
                  onChange={(e) => setNewTask(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter" && newTask.trim()) addTask.mutate(); }}
                />
                <Button size="sm" disabled={!newTask.trim() || addTask.isPending} onClick={() => addTask.mutate()}>
                  Add
                </Button>
              </div>
            )}
          </div>

          {!editable && (
            <div className="text-xs text-mute border-t border-line pt-3">
              Read-only for your role. Ask an admin or your launch lead to edit.
            </div>
          )}
        </div>
      </DialogContent>
      <DialogFooter>
        <Button variant="outline" onClick={onClose}>Close</Button>
        {editable && (
          <Button onClick={() => save.mutate()} disabled={save.isPending}>
            {save.isPending ? "Saving…" : "Save changes"}
          </Button>
        )}
      </DialogFooter>
    </Dialog>
  );
}
