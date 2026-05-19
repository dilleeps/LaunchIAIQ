import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const navGroups: { label: string; items: { to: string; label: string; glyph: string; badge?: string }[] }[] = [
  {
    label: "Portfolio",
    items: [
      { to: "/", label: "Overview", glyph: "◐" },
      { to: "/timeline", label: "Timeline", glyph: "▭" },
      { to: "/matrix", label: "Asset × Country", glyph: "▦" },
      { to: "/dependencies", label: "Dependencies", glyph: "◇" },
      { to: "/risks", label: "Risks", glyph: "◭" },
      { to: "/milestones", label: "Milestones", glyph: "◉" },
    ],
  },
  {
    label: "Workspace",
    items: [
      { to: "/launches", label: "Launches", glyph: "⎙" },
      { to: "/scenarios", label: "Scenarios & IRP", glyph: "⚭" },
      { to: "/reports", label: "Reports", glyph: "▤" },
      { to: "/admin", label: "Settings", glyph: "⚙" },
    ],
  },
];

export function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const initials = (user?.full_name || user?.email || "U")
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="grid h-screen overflow-hidden" style={{ gridTemplateColumns: "240px 1fr", gridTemplateRows: "64px 1fr", gridTemplateAreas: '"topbar topbar" "sidebar main"' }}>
      <header style={{ gridArea: "topbar" }} className="flex items-center gap-8 border-b border-line px-7 bg-paper">
        <div className="flex items-center gap-3.5">
          <div className="w-8 h-8 rounded-full bg-primary grid place-items-center text-paper font-display font-semibold">L</div>
          <div className="font-display text-lg tracking-tight">
            LaunchIA<em className="text-primary not-italic font-normal">IQ</em>
          </div>
        </div>
        <div className="w-px h-6 bg-line" />
        <div className="flex items-center gap-6 font-mono text-[11px] uppercase tracking-wider text-mute">
          <span>Portfolio · <b className="text-ink-2">FY26—FY27</b></span>
          <span>Org · <b className="text-ink-2">{user?.org_id?.slice(0, 8)}</b></span>
        </div>
        <div className="ml-auto flex items-center gap-4">
          <div className="font-mono text-[11px] uppercase tracking-wider text-mute">{user?.email}</div>
          <button
            onClick={() => { logout(); navigate("/login"); }}
            className="w-8 h-8 grid place-items-center rounded-full bg-paper-3 hover:bg-line text-xs font-medium"
            title="Sign out"
          >
            {initials}
          </button>
        </div>
      </header>

      <aside style={{ gridArea: "sidebar" }} className="border-r border-line bg-paper-2 overflow-y-auto py-6">
        {navGroups.map((g) => (
          <div key={g.label} className="px-4 mb-6">
            <div className="font-mono text-[10px] uppercase tracking-widest text-mute px-3 mb-2">{g.label}</div>
            {g.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-3 py-2 rounded text-sm ${
                    isActive ? "bg-primary-soft text-primary font-medium" : "text-ink-2 hover:bg-paper-3"
                  }`
                }
              >
                <span className="text-mute w-4">{item.glyph}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </aside>

      <main style={{ gridArea: "main" }} className="overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
