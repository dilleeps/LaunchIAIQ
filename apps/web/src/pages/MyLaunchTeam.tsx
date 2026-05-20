import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { Select } from "../components/ui/select";

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
  launch_code: string;
  brand: string;
  asset_therapy_area?: string | null;
  country_name: string;
  indication_label?: string | null;
}

interface Filters {
  therapy_areas: string[];
  brands: string[];
  indications: string[];
  countries: { code: string; name: string }[];
}

export function MyLaunchTeam() {
  const [ta, setTa] = useState("");
  const [brand, setBrand] = useState("");
  const [indication, setIndication] = useState("");
  const [country, setCountry] = useState("");
  const [search, setSearch] = useState("");

  const { data: filters } = useQuery({
    queryKey: ["my-team-filters"],
    queryFn: () => api<Filters>("/my-launch-team/filters"),
  });

  const { data: members } = useQuery({
    queryKey: ["my-launch-team", ta, brand, indication, country],
    queryFn: () => {
      const qs = new URLSearchParams();
      if (ta) qs.set("therapy_area", ta);
      if (brand) qs.set("brand", brand);
      if (indication) qs.set("indication", indication);
      if (country) qs.set("country", country);
      const q = qs.toString();
      return api<TeamMember[]>(`/my-launch-team${q ? "?" + q : ""}`);
    },
  });

  const filtered = (members || []).filter((m) => {
    if (!search.trim()) return true;
    const s = search.toLowerCase();
    return (
      (m.full_name || "").toLowerCase().includes(s) ||
      m.role_label.toLowerCase().includes(s) ||
      m.brand.toLowerCase().includes(s) ||
      m.country_name.toLowerCase().includes(s)
    );
  });

  return (
    <>
      <PageHeader
        eyebrow="Workspace"
        title="Welcome to My Launch"
        subtitle="Manage your workspace, team, and settings all in one place. Filter the team roster across therapy areas, brands, indications, and countries."
      />

      <section className="px-10 py-6">
        <div className="bg-card border border-line rounded-lg p-5">
          <div className="font-display text-xl tracking-tight mb-1">My Launch Team</div>
          <div className="text-sm text-mute-2 mb-4">
            Select values from each dropdown below to filter. Use the search box to narrow down further.
          </div>
          <div className="grid grid-cols-12 gap-3 items-center">
            <div className="col-span-2">
              <Select value={ta} onChange={(e) => setTa(e.target.value)}>
                <option value="">All Therapy Areas</option>
                {filters?.therapy_areas.map((t) => <option key={t} value={t}>{t}</option>)}
              </Select>
            </div>
            <div className="col-span-2">
              <Select value={brand} onChange={(e) => setBrand(e.target.value)}>
                <option value="">All Brands</option>
                {filters?.brands.map((b) => <option key={b} value={b}>{b}</option>)}
              </Select>
            </div>
            <div className="col-span-2">
              <Select value={indication} onChange={(e) => setIndication(e.target.value)}>
                <option value="">All Indications</option>
                {filters?.indications.map((i) => <option key={i} value={i}>{i}</option>)}
              </Select>
            </div>
            <div className="col-span-2">
              <Select value={country} onChange={(e) => setCountry(e.target.value)}>
                <option value="">All Countries</option>
                {filters?.countries.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
              </Select>
            </div>
            <div className="col-span-3">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search name, role, brand…"
                className="w-full h-9 px-3 text-sm border border-line rounded focus:outline-none focus:border-primary"
              />
            </div>
            <div className="col-span-1 text-xs text-mute font-mono uppercase tracking-wider text-right">
              {filtered.length} {filtered.length === 1 ? "person" : "people"}
            </div>
          </div>
        </div>
      </section>

      <section className="px-10 pb-12">
        {filtered.length === 0 && (
          <div className="text-center text-mute py-12 border border-dashed border-line rounded-lg">
            No team members match the current filters.
          </div>
        )}
        <div className="grid grid-cols-3 gap-4">
          {filtered.map((m) => <MemberCard key={m.id} m={m} />)}
        </div>
      </section>
    </>
  );
}

function MemberCard({ m }: { m: TeamMember }) {
  const initials = (m.full_name || "?")
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
  return (
    <div className="border border-line rounded-lg p-4 bg-paper hover:border-primary/30 transition">
      <div className="flex items-start gap-3">
        <div className="w-12 h-12 rounded-full bg-primary grid place-items-center text-paper font-semibold">{initials}</div>
        <div className="flex-1">
          <div className="font-medium">{m.full_name || "N/A"}</div>
          <div className="text-xs text-mute-2">{m.role_label}</div>
          <div className="flex items-center gap-1.5 mt-2">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-paper-2 border border-line rounded-full text-[10px] font-mono uppercase tracking-wider">
              <span className="w-1.5 h-1.5 rounded-full bg-primary" />
              {m.country_name}
            </span>
            {m.is_manager && (
              <span className="text-[10px] font-mono uppercase tracking-wider text-primary">Manager</span>
            )}
          </div>
          <div className="text-[10px] text-mute font-mono uppercase tracking-wider mt-1">
            {m.brand} · <Link to={`/launches/${m.launch_id}`} className="text-primary hover:underline">{m.launch_code}</Link>
          </div>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 mt-4">
        <button
          disabled={!m.email}
          className="text-xs px-3 py-1.5 border border-line rounded hover:bg-paper-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
          title={m.email ? `Chat with ${m.full_name}` : "No contact info"}
        >
          💬 Chat
        </button>
        <a
          href={m.email ? `mailto:${m.email}` : undefined}
          aria-disabled={!m.email}
          className={`text-xs px-3 py-1.5 border border-line rounded flex items-center justify-center gap-1.5 ${m.email ? "hover:bg-paper-2" : "opacity-50 cursor-not-allowed"}`}
        >
          ✉️ Email
        </a>
      </div>
    </div>
  );
}
