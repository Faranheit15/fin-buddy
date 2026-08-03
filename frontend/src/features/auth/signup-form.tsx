"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/features/auth/auth-provider";
import { demoLogin, signupWithPassword } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";

export function SignupForm() {
  const router = useRouter();
  const { applyBackendSession, configured } = useAuth();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!configured) {
    return (
      <p className="rounded-lg border border-dashed bg-muted/40 p-3 text-sm text-muted-foreground">
        API URL is not configured in <code className="font-mono text-xs">.env.local</code>.
      </p>
    );
  }

  async function onDemoLogin() {
    setLoading(true);
    setError(null);
    try {
      const res = await demoLogin();
      if (!res.session?.access_token) {
        throw new Error(res.message || "Demo login failed");
      }
      await applyBackendSession(res.session);
      router.replace("/app");
      router.refresh();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Demo login failed",
      );
    } finally {
      setLoading(false);
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      const res = await signupWithPassword(email, password, displayName || undefined);
      if (res.session?.access_token) {
        await applyBackendSession(res.session);
        router.replace("/app");
        router.refresh();
        return;
      }
      setMessage(
        res.message ||
          "Account created. If email confirmation is enabled, confirm then sign in.",
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : err instanceof Error ? err.message : "Sign up failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <Button
        type="button"
        className="w-full"
        size="lg"
        disabled={loading}
        onClick={() => void onDemoLogin()}
      >
        Continue as demo
      </Button>
      <p className="text-center text-[11px] text-muted-foreground">
        Skip Supabase email limits and explore the app with a local demo user.
      </p>
      <div className="relative py-1 text-center text-xs text-muted-foreground">
        <span className="relative z-10 bg-card px-2">or create a real account</span>
        <div className="absolute inset-x-0 top-1/2 h-px bg-border" />
      </div>
    <form className="space-y-3" onSubmit={(e) => void onSubmit(e)}>
      <div className="space-y-1.5">
        <Label htmlFor="displayName">Display name</Label>
        <Input
          id="displayName"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder="Your name"
          autoComplete="name"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
          placeholder="you@example.com"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="new-password"
          placeholder="At least 8 characters"
        />
      </div>

      {error && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
      )}
      {message && (
        <p className="rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">{message}</p>
      )}

      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? "Creating…" : "Create account"}
      </Button>

      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-foreground underline-offset-4 hover:underline">
          Sign in
        </Link>
      </p>
      <p className="text-center text-[11px] text-muted-foreground">
        Signup is processed by the Fin Buddy API using server-side Supabase credentials.
      </p>
    </form>
    </div>
  );
}
