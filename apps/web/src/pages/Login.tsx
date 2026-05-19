import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@demo.example");
  const [password, setPassword] = useState("demo123");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      navigate("/");
    } catch (err: any) {
      setError("Invalid credentials");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen grid place-items-center bg-paper-2">
      <div className="w-[400px] bg-paper border border-line rounded-lg p-10">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-full bg-accent grid place-items-center text-paper font-display font-semibold text-xl">L</div>
          <div>
            <div className="font-display text-2xl tracking-tight">
              LaunchIA<em className="text-accent not-italic font-normal">IQ</em>
            </div>
            <div className="font-mono text-[10px] uppercase tracking-widest text-mute">Pharma launch cockpit</div>
          </div>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-mute mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-line rounded focus:outline-none focus:border-accent"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-mute mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-line rounded focus:outline-none focus:border-accent"
              required
            />
          </div>
          {error && <div className="text-accent text-sm">{error}</div>}
          <button
            disabled={busy}
            className="w-full py-2.5 bg-accent text-paper rounded hover:bg-accent-dark transition disabled:opacity-50"
          >
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <div className="mt-6 text-xs text-mute font-mono">
          Demo: admin@demo.example / demo123
        </div>
      </div>
    </div>
  );
}
