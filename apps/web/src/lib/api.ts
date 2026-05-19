const BASE = "/api";

function getToken(): string | null {
  return localStorage.getItem("launchiq_token");
}

export function setToken(t: string | null) {
  if (t) localStorage.setItem("launchiq_token", t);
  else localStorage.removeItem("launchiq_token");
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  const tok = getToken();
  if (tok) headers.set("Authorization", `Bearer ${tok}`);
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
