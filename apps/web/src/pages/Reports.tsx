import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, Cell, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../lib/api";
import type { Forecast, Launch } from "../lib/types";
import { PageHeader } from "../components/PageHeader";
import { Card } from "../components/ui/card";

export function Reports() {
  const { data: launches } = useQuery({ queryKey: ["launches"], queryFn: () => api<Launch[]>("/launches") });

  return (
    <>
      <PageHeader
        eyebrow="Reports"
        title="Portfolio analytics."
        subtitle="Forecast revenue by launch, sensitivity ranges and variance vs actuals. Export to PDF/Excel ships in Phase 2."
      />
      <div className="px-10 py-6 space-y-8">
        <PortfolioRevenue launches={launches || []} />
        {launches?.[0] && <SensitivityCard launchId={launches[0].id} brand={launches[0].asset.brand_name} />}
        {launches?.find((l) => l.launch_phase === "Launch") && (
          <VarianceCard launch={launches.find((l) => l.launch_phase === "Launch")!} />
        )}
      </div>
    </>
  );
}

function PortfolioRevenue({ launches }: { launches: Launch[] }) {
  const { data: allFc } = useQuery({
    queryKey: ["all-forecasts", launches.map((l) => l.id).join(",")],
    queryFn: async () => {
      const results = await Promise.all(
        launches.map(async (l) => ({ launch: l, fc: await api<Forecast[]>(`/launches/${l.id}/forecast`) }))
      );
      return results;
    },
    enabled: launches.length > 0,
  });
  const data = (allFc || []).map(({ launch, fc }) => {
    const current = fc.find((f) => f.is_current) ?? fc[0];
    const y1 = current?.y1_patients && current?.y1_net_price ? current.y1_patients * current.y1_net_price : 0;
    const y2 = current?.y2_patients && current?.y2_net_price ? current.y2_patients * current.y2_net_price : 0;
    const y3 = current?.y3_patients && current?.y3_net_price ? current.y3_patients * current.y3_net_price : 0;
    return { launch_code: launch.launch_code, brand: launch.asset.brand_name, country: launch.country.code, y1: y1 / 1e6, y2: y2 / 1e6, y3: y3 / 1e6, ccy: current?.currency || "USD" };
  });
  return (
    <Card className="p-6">
      <h2 className="font-display text-xl tracking-tight mb-4">Forecast revenue by launch (M, local currency)</h2>
      <div className="h-72">
        <ResponsiveContainer>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E5" />
            <XAxis dataKey="launch_code" tick={{ fontSize: 11, fontFamily: "JetBrains Mono" }} />
            <YAxis tick={{ fontSize: 11, fontFamily: "JetBrains Mono" }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="y1" fill="#165d59" name="Year 1" />
            <Bar dataKey="y2" fill="#2F7D4F" name="Year 2" />
            <Bar dataKey="y3" fill="#B8740A" name="Year 3" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

interface SensitivityResp {
  launch_id: string;
  forecast_id: string;
  scenarios: {
    scenario: "low" | "base" | "high";
    factors: { penetration: number; price: number; share: number };
    currency: string;
    years: { year: number; patients: number; net_price: number; revenue: number }[];
    total_revenue: number;
  }[];
}

function SensitivityCard({ launchId, brand }: { launchId: string; brand: string }) {
  const { data, error } = useQuery({
    queryKey: ["sensitivity", launchId],
    queryFn: () => api<SensitivityResp>(`/launches/${launchId}/sensitivity`),
    retry: false,
  });
  if (error || !data) return null;
  const chart = data.scenarios.map((s) => ({
    scenario: s.scenario,
    y1: (s.years[0]?.revenue ?? 0) / 1e6,
    y2: (s.years[1]?.revenue ?? 0) / 1e6,
    y3: (s.years[2]?.revenue ?? 0) / 1e6,
    total: s.total_revenue / 1e6,
  }));
  return (
    <Card className="p-6">
      <h2 className="font-display text-xl tracking-tight mb-1">Sensitivity — {brand}</h2>
      <p className="text-sm text-mute-2 mb-4">Low / base / high revenue scenarios computed from price and penetration drivers.</p>
      <div className="h-64">
        <ResponsiveContainer>
          <BarChart data={chart}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E5" />
            <XAxis dataKey="scenario" tick={{ fontSize: 11, fontFamily: "JetBrains Mono" }} />
            <YAxis tick={{ fontSize: 11, fontFamily: "JetBrains Mono" }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="y1" name="Y1 (M)" fill="#165d59">
              {chart.map((_, i) => <Cell key={i} fill={["#C8102E", "#165d59", "#2F7D4F"][i]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

interface VarianceAlert {
  id: string;
  period: string;
  metric: string;
  forecast_value: number;
  actual_value: number;
  variance_pct: number;
  status: string;
}

function VarianceCard({ launch }: { launch: Launch }) {
  const { data, error } = useQuery({
    queryKey: ["variance", launch.id],
    queryFn: () => api<VarianceAlert[]>(`/launches/${launch.id}/variance-alerts`),
    retry: false,
  });
  if (error || !data || data.length === 0) return null;
  return (
    <Card className="p-6">
      <h2 className="font-display text-xl tracking-tight mb-1">Variance alerts — {launch.asset.brand_name}</h2>
      <p className="text-sm text-mute-2 mb-4">Actuals vs forecast, auto-flagged when variance exceeds the configured threshold.</p>
      <table className="w-full text-sm">
        <thead className="bg-paper-2 border-y border-line text-left">
          <tr>
            <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Period</th>
            <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Metric</th>
            <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Forecast</th>
            <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Actual</th>
            <th className="p-3 font-mono uppercase text-[10px] tracking-widest text-mute">Variance</th>
          </tr>
        </thead>
        <tbody>
          {data.map((a) => (
            <tr key={a.id} className="border-b border-line last:border-0">
              <td className="p-3 font-mono">{a.period}</td>
              <td className="p-3">{a.metric}</td>
              <td className="p-3 font-mono text-xs">{a.forecast_value.toLocaleString()}</td>
              <td className="p-3 font-mono text-xs">{a.actual_value.toLocaleString()}</td>
              <td className={`p-3 font-mono text-xs ${Math.abs(a.variance_pct) >= 10 ? "text-destructive" : ""}`}>
                {a.variance_pct >= 0 ? "+" : ""}{a.variance_pct.toFixed(1)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
