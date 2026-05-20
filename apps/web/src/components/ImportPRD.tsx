import { useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "./ui/button";

interface ImportResult {
  imported: number;
  launches: { id: string; launch_code: string; brand: string; country: string }[];
}

export function ImportPRD() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ImportResult | string | null>(null);
  const qc = useQueryClient();

  async function handle(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setResult(null);
    const form = new FormData();
    form.append("file", file);
    const tok = localStorage.getItem("launchiq_token");
    try {
      const res = await fetch("/api/prd/import", {
        method: "POST",
        body: form,
        headers: tok ? { Authorization: `Bearer ${tok}` } : {},
      });
      if (!res.ok) {
        setResult(await res.text());
      } else {
        const r: ImportResult = await res.json();
        setResult(r);
        qc.invalidateQueries();
      }
    } catch (err: any) {
      setResult(String(err));
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <>
      <input ref={inputRef} type="file" accept=".xlsx" className="hidden" onChange={handle} />
      <Button variant="outline" onClick={() => inputRef.current?.click()} disabled={busy}>
        {busy ? "Importing…" : "↥ Import PRD"}
      </Button>
      {result && (
        <div
          className="fixed bottom-6 right-6 max-w-md p-4 bg-card border border-line rounded-lg shadow-lg z-50 cursor-pointer"
          onClick={() => setResult(null)}
        >
          {typeof result === "string" ? (
            <div className="text-sm text-destructive">{result}</div>
          ) : (
            <>
              <div className="font-display text-lg tracking-tight mb-2">
                Imported {result.imported} launch{result.imported === 1 ? "" : "es"}
              </div>
              <ul className="text-xs space-y-1 font-mono">
                {result.launches.map((l) => (
                  <li key={l.id}>
                    {l.launch_code} · {l.brand} · {l.country}
                  </li>
                ))}
              </ul>
              <div className="text-xs text-mute mt-3">Click to dismiss.</div>
            </>
          )}
        </div>
      )}
    </>
  );
}
