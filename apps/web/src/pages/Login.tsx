import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "../hooks/useAuth";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "../components/ui/form";

const schema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});
type Values = z.infer<typeof schema>;

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [submitError, setSubmitError] = useState<string | null>(null);

  const form = useForm<Values>({
    resolver: zodResolver(schema) as any,
    defaultValues: { email: "admin@demo.example", password: "demo123" },
  });

  async function onSubmit(values: Values) {
    setSubmitError(null);
    try {
      await login(values.email, values.password);
      navigate("/");
    } catch {
      setSubmitError("Invalid credentials");
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-[1.15fr_1fr] bg-paper">
      {/* ─── Left: editorial hero ─── */}
      <aside className="relative hidden lg:flex flex-col justify-between bg-ink text-paper p-12 overflow-hidden">
        {/* subtle vignette grid */}
        <div
          className="absolute inset-0 opacity-[0.04] pointer-events-none"
          style={{
            backgroundImage:
              "linear-gradient(to right, #fff 1px, transparent 1px), linear-gradient(to bottom, #fff 1px, transparent 1px)",
            backgroundSize: "32px 32px",
          }}
        />
        {/* primary accent glow */}
        <div className="absolute -top-32 -right-32 w-[480px] h-[480px] rounded-full bg-primary/20 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-[360px] h-[360px] rounded-full bg-primary/10 blur-3xl pointer-events-none" />

        {/* top: wordmark */}
        <header className="relative flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary grid place-items-center text-primary-foreground font-display font-semibold text-xl">
            L
          </div>
          <div className="font-display text-2xl tracking-tight">
            Launch<em className="text-primary not-italic font-normal">AIQ</em>
          </div>
          <span className="ml-3 px-2 py-0.5 rounded-full border border-paper/15 text-[10px] font-mono uppercase tracking-widest text-paper/60">
            v0.3 · Pharma cockpit
          </span>
        </header>

        {/* middle: pitch */}
        <div className="relative max-w-xl space-y-6">
          <div className="font-mono text-[10px] uppercase tracking-widest text-paper/50">
            Drug launch management · Portfolio · FY26—FY27
          </div>
          <h1 className="font-display text-5xl xl:text-6xl leading-[1.05] tracking-tight">
            One cockpit for every <em className="text-primary not-italic font-normal">launch</em>,
            every market, every milestone.
          </h1>
          <p className="text-paper/70 text-lg leading-relaxed max-w-md">
            Hierarchical PRDs, configurable launch frameworks, real-time market
            intelligence from openFDA · ClinicalTrials · DailyMed, and field-level
            audit — purpose-built for global brand teams.
          </p>

          {/* feature chips */}
          <div className="flex flex-wrap gap-2 pt-2">
            {[
              "Asset × Country matrix",
              "Regulatory pathways",
              "IRP simulator",
              "Field-level RBAC",
              "Launch framework V8",
              "P&L vs forecast",
            ].map((c) => (
              <span
                key={c}
                className="px-3 py-1.5 rounded-full border border-paper/15 bg-paper/5 backdrop-blur text-xs text-paper/85"
              >
                {c}
              </span>
            ))}
          </div>

          {/* mini stat strip — editorial cockpit feel */}
          <div className="grid grid-cols-3 gap-px bg-paper/10 mt-8 rounded-lg overflow-hidden border border-paper/10">
            <Stat label="Active launches" value="15" note="3 assets · 5 markets" />
            <Stat label="Modelled peak" value="$1.2 B" note="3-yr horizon" />
            <Stat label="Open risks" value="07" note="Score ≥ 6 (L×I)" />
          </div>
        </div>

        {/* bottom: legal / trust strip */}
        <footer className="relative flex items-center justify-between text-[10px] font-mono uppercase tracking-widest text-paper/40">
          <span>SOC 2 · 21 CFR Part 11 ready · Multi-tenant</span>
          <span>© {new Date().getFullYear()} LaunchAIQ</span>
        </footer>
      </aside>

      {/* ─── Right: auth ─── */}
      <main className="grid place-items-center p-6 lg:p-12 bg-paper">
        <div className="w-full max-w-sm">
          {/* mobile-only wordmark */}
          <div className="flex lg:hidden items-center gap-3 mb-10">
            <div className="w-10 h-10 rounded-full bg-primary grid place-items-center text-primary-foreground font-display font-semibold text-xl">
              L
            </div>
            <div className="font-display text-2xl tracking-tight">
              Launch<em className="text-primary not-italic font-normal">AIQ</em>
            </div>
          </div>

          <div className="mb-8">
            <div className="font-mono text-[10px] uppercase tracking-widest text-mute mb-3">
              Sign in
            </div>
            <h2 className="font-display text-3xl tracking-tight">
              Welcome back.
            </h2>
            <p className="text-sm text-mute-2 mt-2">
              Continue to your portfolio cockpit.
            </p>
          </div>

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-mono text-[10px] uppercase tracking-widest text-mute">
                      Email
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        autoComplete="email"
                        placeholder="you@company.com"
                        className="h-11 text-base"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <div className="flex items-center justify-between">
                      <FormLabel className="font-mono text-[10px] uppercase tracking-widest text-mute">
                        Password
                      </FormLabel>
                      <button
                        type="button"
                        className="text-[11px] text-mute hover:text-primary font-mono uppercase tracking-wider"
                        onClick={(e) => e.preventDefault()}
                      >
                        Forgot?
                      </button>
                    </div>
                    <FormControl>
                      <Input
                        type="password"
                        autoComplete="current-password"
                        placeholder="••••••••"
                        className="h-11 text-base"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {submitError && (
                <div className="text-xs text-destructive bg-destructive/5 border border-destructive/20 rounded px-3 py-2">
                  {submitError}
                </div>
              )}

              <Button
                type="submit"
                disabled={form.formState.isSubmitting}
                className="w-full h-11 font-mono uppercase tracking-wider text-[11px]"
              >
                {form.formState.isSubmitting ? "Signing in…" : "Sign in →"}
              </Button>

              <div className="relative flex items-center gap-3 py-2">
                <div className="flex-1 h-px bg-line" />
                <span className="font-mono text-[10px] uppercase tracking-widest text-mute">
                  or
                </span>
                <div className="flex-1 h-px bg-line" />
              </div>

              <button
                type="button"
                disabled
                className="w-full h-11 border border-line rounded-md text-sm font-medium text-mute-2 hover:bg-paper-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                title="SAML / OIDC SSO available in Phase 2"
              >
                <span className="font-mono text-[10px] uppercase tracking-widest">SSO</span>
                <span className="text-xs">— Okta · Azure AD · Ping</span>
              </button>
            </form>
          </Form>

          <div className="mt-10 p-3 rounded-md bg-paper-2 border border-line">
            <div className="font-mono text-[10px] uppercase tracking-widest text-mute mb-1">
              Demo credentials
            </div>
            <div className="text-xs text-ink-2 font-mono">
              admin@demo.example · demo123
            </div>
          </div>

          <div className="mt-8 text-[11px] text-mute font-mono uppercase tracking-wider">
            New here?{" "}
            <a className="text-primary hover:underline" href="mailto:hello@launchaiq.com">
              Request a demo →
            </a>
          </div>
        </div>
      </main>
    </div>
  );
}

function Stat({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="bg-ink p-4">
      <div className="font-mono text-[9px] uppercase tracking-widest text-paper/40">{label}</div>
      <div className="font-display text-2xl tracking-tight mt-1">{value}</div>
      <div className="text-[10px] text-paper/50 font-mono uppercase tracking-wider mt-1">{note}</div>
    </div>
  );
}
