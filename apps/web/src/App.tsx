import { useEffect } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppShell } from "./layouts/AppShell";
import { Login } from "./pages/Login";
import { Overview } from "./pages/Overview";
import { Matrix } from "./pages/Matrix";
import { Milestones } from "./pages/Milestones";
import { LaunchDetail } from "./pages/LaunchDetail";
import { LaunchList } from "./pages/LaunchList";
import { Settings } from "./pages/Settings";
import { Timeline } from "./pages/Timeline";
import { DependenciesGraph } from "./pages/DependenciesGraph";
import { Scenarios } from "./pages/Scenarios";
import { Risks } from "./pages/Risks";
import { Reports } from "./pages/Reports";
import { CompetitiveIntel } from "./pages/CompetitiveIntel";
import { Audit } from "./pages/Audit";
import { useAuth } from "./hooks/useAuth";

const qc = new QueryClient({ defaultOptions: { queries: { staleTime: 30_000 } } });

function RequireAuth({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  const loc = useLocation();
  if (loading) return <div className="grid place-items-center h-screen text-mute">Loading…</div>;
  if (!user) return <Navigate to="/login" state={{ from: loc }} replace />;
  return children;
}

export default function App() {
  const hydrate = useAuth((s) => s.hydrate);
  useEffect(() => { hydrate(); }, [hydrate]);

  return (
    <QueryClientProvider client={qc}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<RequireAuth><AppShell /></RequireAuth>}>
          <Route index element={<Overview />} />
          <Route path="timeline" element={<Timeline />} />
          <Route path="matrix" element={<Matrix />} />
          <Route path="dependencies" element={<DependenciesGraph />} />
          <Route path="risks" element={<Risks />} />
          <Route path="milestones" element={<Milestones />} />
          <Route path="scenarios" element={<Scenarios />} />
          <Route path="launches" element={<LaunchList />} />
          <Route path="launches/:id" element={<LaunchDetail />} />
          <Route path="reports" element={<Reports />} />
          <Route path="competitive-intel" element={<CompetitiveIntel />} />
          <Route path="competitive-intel/:assetId" element={<CompetitiveIntel />} />
          <Route path="audit" element={<Audit />} />
          <Route path="admin" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </QueryClientProvider>
  );
}
