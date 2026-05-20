import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { api } from "../lib/api";
import type { Asset } from "../lib/types";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Select } from "./ui/select";

interface SyncResult {
  asset_name: string;
  therapeutic_area: string | null;
  ran: { kind: string; ok?: boolean; ingested?: number; error?: string }[];
  total_intel_records_matching: number;
}

export function SyncIntelByAsset() {
  const qc = useQueryClient();
  const [assetId, setAssetId] = useState("");
  const [result, setResult] = useState<SyncResult | null>(null);

  const { data: assets } = useQuery({
    queryKey: ["assets"],
    queryFn: () => api<Asset[]>("/assets"),
  });

  const sync = useMutation({
    mutationFn: () => api<SyncResult>(`/intel/sync-asset/${assetId}`, { method: "POST" }),
    onSuccess: (r) => {
      setResult(r);
      qc.invalidateQueries({ queryKey: ["conns"] });
      qc.invalidateQueries({ queryKey: ["ci-portfolio"] });
      qc.invalidateQueries({ queryKey: ["ci-asset"] });
    },
  });

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="font-display text-lg tracking-tight">Sync intel by drug</div>
          <p className="text-xs text-mute-2 mt-1">
            Pull the latest openFDA labels + recalls, ClinicalTrials.gov updates and DailyMed labels
            for a single asset. Auto-creates connectors if missing.
          </p>
        </div>
      </div>
      <div className="flex gap-2 items-end">
        <div className="flex-1">
          <label className="block text-[10px] font-mono uppercase tracking-widest text-mute mb-1">Drug / Asset</label>
          <Select value={assetId} onChange={(e) => setAssetId(e.target.value)}>
            <option value="">Choose an asset…</option>
            {assets?.map((a) => (
              <option key={a.id} value={a.id}>
                {a.brand_name}
                {a.therapeutic_area ? ` — ${a.therapeutic_area}` : ""}
                {a.inn ? ` (${a.inn})` : ""}
              </option>
            ))}
          </Select>
        </div>
        <Button
          onClick={() => sync.mutate()}
          disabled={!assetId || sync.isPending}
        >
          <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${sync.isPending ? "animate-spin" : ""}`} />
          {sync.isPending ? "Syncing…" : "Sync intel now"}
        </Button>
      </div>

      {result && (
        <div className="mt-4 border-t border-line pt-4">
          <div className="font-mono text-[11px] uppercase tracking-widest text-mute mb-2">
            Sync result · {result.asset_name}
          </div>
          <ul className="text-sm space-y-1 mb-2">
            {result.ran.map((r) => (
              <li key={r.kind} className="flex items-center gap-2">
                <span className={`chip ${r.ok ? "rag-Green" : "rag-Red"}`}>
                  {r.ok ? "ok" : "error"}
                </span>
                <span className="font-mono text-xs">{r.kind}</span>
                <span className="text-mute-2">
                  {r.ok
                    ? `${r.ingested ?? 0} new record${r.ingested === 1 ? "" : "s"}`
                    : (r.error ?? "failed")}
                </span>
              </li>
            ))}
          </ul>
          <div className="text-xs text-mute-2">
            Total intel records matching this asset/TA: <b>{result.total_intel_records_matching}</b>.
            Surfaced under <i>Competitive intel → {result.asset_name}</i> and each Launch's <i>Market Pulse</i> tab.
          </div>
        </div>
      )}
    </Card>
  );
}
