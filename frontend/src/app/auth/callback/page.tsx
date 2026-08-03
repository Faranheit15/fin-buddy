"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { useAuth } from "@/features/auth/auth-provider";
import { establishSessionFromTokens } from "@/lib/api/auth";

/**
 * OAuth / magic-link return page.
 * Tokens arrive in the URL (query or hash) from Supabase Hosted Auth.
 * We immediately hand them to the FastAPI backend to validate + bootstrap profile,
 * then store cookies on this origin. No browser Supabase client is used.
 */
function CallbackInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { applyBackendSession } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const next = searchParams.get("next") || "/app";

        // Hash tokens: #access_token=...&refresh_token=...
        const hash = typeof window !== "undefined" ? window.location.hash.replace(/^#/, "") : "";
        const hashParams = new URLSearchParams(hash);
        const queryAccess = searchParams.get("access_token");
        const accessToken =
          hashParams.get("access_token") || queryAccess || searchParams.get("token");
        const refreshToken =
          hashParams.get("refresh_token") || searchParams.get("refresh_token");
        const expiresIn = hashParams.get("expires_in") || searchParams.get("expires_in");
        const expiresAt = hashParams.get("expires_at") || searchParams.get("expires_at");

        if (!accessToken) {
          // Authorization code without tokens — cannot complete without client PKCE.
          // Ask user to use password/OTP instead, or configure implicit redirect.
          throw new Error(
            "No access token in callback URL. Use email/password or OTP, or ensure the OAuth redirect includes tokens.",
          );
        }

        const backend = await establishSessionFromTokens({
          access_token: accessToken,
          refresh_token: refreshToken,
          expires_in: expiresIn ? Number(expiresIn) : null,
          expires_at: expiresAt ? Number(expiresAt) : null,
        });

        if (!backend.session?.access_token) {
          throw new Error(backend.message || "Backend rejected session tokens");
        }

        await applyBackendSession(backend.session);
        if (!cancelled) {
          // Clear tokens from the address bar
          window.history.replaceState({}, "", "/auth/callback");
          router.replace(next.startsWith("/") ? next : "/app");
          router.refresh();
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Auth callback failed");
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [applyBackendSession, router, searchParams]);

  if (error) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center gap-3 px-6 py-16">
        <p className="max-w-md text-center text-sm text-destructive">{error}</p>
        <a href="/login" className="text-sm font-medium underline-offset-4 hover:underline">
          Back to sign in
        </a>
      </main>
    );
  }

  return (
    <main className="flex flex-1 items-center justify-center px-6 py-16">
      <p className="text-sm text-muted-foreground">Completing sign-in…</p>
    </main>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <main className="flex flex-1 items-center justify-center px-6 py-16">
          <p className="text-sm text-muted-foreground">Completing sign-in…</p>
        </main>
      }
    >
      <CallbackInner />
    </Suspense>
  );
}
