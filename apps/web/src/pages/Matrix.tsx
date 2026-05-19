import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import type { Country, MatrixRow } from "../lib/types";
import { PageHeader, RagChip } from "../components/PageHeader";

export function Matrix() {
  const navigate = useNavigate();
  const { data: rows } = useQuery({
    queryKey: ["matrix"],
    queryFn: () => api<MatrixRow[]>("/portfolio/matrix"),
  });
  const { data: countries } = useQuery({
    queryKey: ["countries"],
    queryFn: () => api<Country[]>("/lookups/countries"),
  });

  const visibleCodes = Array.from(
    new Set((rows || []).flatMap((r) => Object.keys(r.cells)))
  ).sort();
  const visibleCountries = (countries || []).filter((c) => visibleCodes.includes(c.code));

  return (
    <>
      <PageHeader
        eyebrow="Asset × Country Matrix"
        title="The portfolio grid."
        subtitle="RAG and readiness % for every Asset × Country combination. Click any cell to drill into the launch."
      />
      <div className="px-10 py-8">
        <div className="border border-line rounded-lg overflow-hidden bg-paper">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-paper-2">
                <th className="text-left p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Asset</th>
                {visibleCountries.map((c) => (
                  <th key={c.code} className="p-3 text-left font-mono uppercase text-[10px] tracking-widest text-mute">
                    <div>{c.name}</div>
                    <div className="text-[9px] text-mute opacity-70 mt-0.5">{c.hta_body}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows?.map((row) => (
                <tr key={row.asset_id} className="border-b border-line last:border-0">
                  <td className="p-3 font-display text-lg">{row.brand_name}</td>
                  {visibleCountries.map((c) => {
                    const cell = row.cells[c.code];
                    if (!cell) {
                      return <td key={c.code} className="p-3 text-mute text-xs">—</td>;
                    }
                    return (
                      <td key={c.code} className="p-3">
                        <button
                          onClick={() => navigate(`/launches/${cell.launch_id}`)}
                          className="w-full text-left rounded p-2.5 border border-line hover:border-line-dark transition bg-paper"
                        >
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="font-mono text-[10px] uppercase tracking-wider text-mute">{cell.launch_code}</span>
                            <RagChip rag={cell.rag} />
                          </div>
                          <div className="font-mono text-xs">{cell.milestones_complete_pct}% complete</div>
                        </button>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
