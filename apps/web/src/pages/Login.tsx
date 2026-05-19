import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "../hooks/useAuth";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "../components/ui/form";
import { Card } from "../components/ui/card";

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
    <div className="min-h-screen grid place-items-center bg-paper-2">
      <Card className="w-[400px] p-10">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-full bg-primary grid place-items-center text-primary-foreground font-display font-semibold text-xl">L</div>
          <div>
            <div className="font-display text-2xl tracking-tight">
              LaunchIA<em className="text-primary not-italic font-normal">IQ</em>
            </div>
            <div className="font-mono text-[10px] uppercase tracking-widest text-mute">Pharma launch cockpit</div>
          </div>
        </div>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input type="email" autoComplete="email" {...field} />
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
                  <FormLabel>Password</FormLabel>
                  <FormControl>
                    <Input type="password" autoComplete="current-password" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {submitError && <p className="text-xs text-destructive">{submitError}</p>}
            <Button type="submit" disabled={form.formState.isSubmitting} className="w-full">
              {form.formState.isSubmitting ? "Signing in…" : "Sign in"}
            </Button>
          </form>
        </Form>
        <div className="mt-6 text-xs text-mute font-mono">Demo: admin@demo.example / demo123</div>
      </Card>
    </div>
  );
}
