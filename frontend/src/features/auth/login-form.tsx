"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/features/auth/auth-provider";
import {
  demoLogin,
  getGoogleOAuthUrl,
  loginWithPassword,
  requestMagicLink,
  verifyOtp,
} from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import {
  generateOAuthState,
  generatePKCEPair,
  sanitizeAppPath,
  storeOAuthFlow,
} from "@/lib/auth/oauth";
import { env } from "@/lib/env";
import { cn } from "@/lib/utils";

type Mode = "password" | "magic";

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") || "/app";
  const { applyEstablishedSession } = useAuth();

  const [mode, setMode] = useState<Mode>("password");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function finishAuth() {
    await applyEstablishedSession();
    router.replace(next);
    router.refresh();
  }

  async function onPasswordLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      const res = await loginWithPassword(email, password);
      if (!res.session?.authenticated) {
        throw new Error(res.message || "No session returned from backend");
      }
      await finishAuth();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Sign in failed",
      );
    } finally {
      setLoading(false);
    }
  }

  async function onMagicLink(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      if (otpSent && otp) {
        const res = await verifyOtp({
          email,
          token: otp,
          type: "email",
        });
        if (!res.session?.authenticated) {
          throw new Error(res.message || "Verification failed");
        }
        await finishAuth();
        return;
      }

      await requestMagicLink(email, `${env.NEXT_PUBLIC_APP_URL}/auth/callback`);
      setOtpSent(true);
      setMessage(
        "If the email is valid, a login code / magic link was sent. Enter the OTP below, or open the link in the email.",
      );
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Request failed",
      );
    } finally {
      setLoading(false);
    }
  }

  async function onGoogle() {
    setLoading(true);
    setError(null);
    try {
      const safeNext = sanitizeAppPath(next);
      const { codeVerifier, codeChallenge } = await generatePKCEPair();
      const state = generateOAuthState();
      storeOAuthFlow({
        state,
        codeVerifier,
        next: safeNext,
        createdAt: Date.now(),
      });

      const callbackUrl = `${env.NEXT_PUBLIC_APP_URL}/auth/callback`;
      const { url } = await getGoogleOAuthUrl({
        redirectTo: callbackUrl,
        codeChallenge,
      });
      window.location.href = url;
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Google sign-in failed",
      );
      setLoading(false);
    }
  }

  async function onDemoLogin() {
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      const res = await demoLogin();
      if (!res.session?.authenticated) {
        throw new Error(res.message || "Demo login failed");
      }
      await finishAuth();
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
        Skips Supabase email (use this while rate-limited). Dev only.
      </p>

      <div className="relative py-1 text-center text-xs text-muted-foreground">
        <span className="relative z-10 bg-card px-2">or real auth</span>
        <div className="absolute inset-x-0 top-1/2 h-px bg-border" />
      </div>

      <Button
        type="button"
        className="w-full"
        variant="outline"
        disabled={loading}
        onClick={() => void onGoogle()}
      >
        Continue with Google
      </Button>

      <div className="relative py-1 text-center text-xs text-muted-foreground">
        <span className="relative z-10 bg-card px-2">or email via API</span>
        <div className="absolute inset-x-0 top-1/2 h-px bg-border" />
      </div>

      <div className="flex gap-1 rounded-lg border bg-muted/40 p-1">
        <button
          type="button"
          className={cn(
            "flex-1 rounded-md px-2 py-1.5 text-xs font-medium transition-colors",
            mode === "password" ? "bg-background shadow-sm" : "text-muted-foreground",
          )}
          onClick={() => setMode("password")}
        >
          Password
        </button>
        <button
          type="button"
          className={cn(
            "flex-1 rounded-md px-2 py-1.5 text-xs font-medium transition-colors",
            mode === "magic" ? "bg-background shadow-sm" : "text-muted-foreground",
          )}
          onClick={() => setMode("magic")}
        >
          Magic link / OTP
        </button>
      </div>

      <form
        className="space-y-3"
        onSubmit={(e) => void (mode === "password" ? onPasswordLogin(e) : onMagicLink(e))}
      >
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </div>

        {mode === "password" && (
          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>
        )}

        {mode === "magic" && otpSent && (
          <div className="space-y-1.5">
            <Label htmlFor="otp">Email OTP code</Label>
            <Input
              id="otp"
              inputMode="numeric"
              autoComplete="one-time-code"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              placeholder="6-digit code"
            />
          </div>
        )}

        {error && (
          <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
        )}
        {message && (
          <p className="rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">{message}</p>
        )}

        <Button type="submit" className="w-full" disabled={loading}>
          {loading
            ? "Please wait…"
            : mode === "password"
              ? "Sign in"
              : otpSent && otp
                ? "Verify code"
                : "Send login code"}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        No account?{" "}
        <Link
          href="/signup"
          className="font-medium text-foreground underline-offset-4 hover:underline"
        >
          Create one
        </Link>
      </p>
      <p className="text-center text-[11px] text-muted-foreground">
        Authentication is handled by the Fin Buddy API (Supabase credentials stay on the server).
      </p>
    </div>
  );
}
