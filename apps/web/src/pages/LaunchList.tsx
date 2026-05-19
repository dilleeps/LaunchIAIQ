import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { Launch } from "../lib/types";
import { PageHeader, RagChip } from "../components/PageHeader";

export function LaunchList() {
  const { data } = useQuery({ queryKey: ["launches"], queryFn: () => api<Launch[]>("/launches") });
  return (
    <>
      <PageHeader eyebrow="Workspace" title="All launches." subtitle="One row per Asset × Country launch." />
      <div className="px-10 py-8">
        <div className="border border-line rounded bg-paper overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-paper-2 border-b border-line text-left">
              <tr>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Code</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Asset</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Country</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Type</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Phase</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Target</th>
                <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">RAG</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((ln) => (
                <tr key={ln.id} className="border-b border-line last:border-0 hover:bg-paper-2">
                  <td className="p-3 font-mono"><Link className="text-accent hover:underline" to={`/launches/${ln.id}`}>{ln.launch_code}</Link></td>
                  <td className="p-3">{ln.asset.brand_name}</td>
                  <td className="p-3">{ln.country.name}</td>
                  <td className="p-3 text-mute-2">{ln.launch_type}</td>
                  <td className="p-3 text-mute-2">{ln.launch_phase}</td>
                  <td className="p-3 font-mono text-xs">{ln.target_launch_date}</td>
                  <td className="p-3"><RagChip rag={ln.overall_rag} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
