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
import { Admin } from "./pages/Admin";
import { Stub } from "./pages/Stub";
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
          <Route path="matrix" element={<Matrix />} />
          <Route path="milestones" element={<Milestones />} />
          <Route path="launches" element={<LaunchList />} />
          <Route path="launches/:id" element={<LaunchDetail />} />
          <Route path="admin" element={<Admin />} />
          <Route path="timeline" element={<Stub title="Timeline." message="Gantt-style view of all launches across FY26-FY27. Critical path highlighted from the dependencies graph." />} />
          <Route path="dependencies" element={<Stub title="Dependencies graph." message="Force-directed visualisation of every typed link in the portfolio. Click a node to see what depends on it." />} />
          <Route path="risks" element={<Stub title="Portfolio risks." message="Cross-launch risk register with likelihood × impact scoring, sortable by score and ageing." />} />
          <Route path="reports" element={<Stub title="Reports." message="PDF / Excel exports of any view, scheduled distribution to stakeholders." />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </QueryClientProvider>
  );
}
