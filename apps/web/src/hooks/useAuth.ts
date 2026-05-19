import { create } from "zustand";
import { api, setToken } from "../lib/api";
import type { User } from "../lib/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hydrate: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  loading: true,
  async login(email, password) {
    const { access_token } = await api<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(access_token);
    const me = await api<User>("/auth/me");
    set({ user: me });
  },
  logout() {
    setToken(null);
    set({ user: null });
  },
  async hydrate() {
    try {
      const me = await api<User>("/auth/me");
      set({ user: me, loading: false });
    } catch {
      set({ user: null, loading: false });
    }
  },
}));
