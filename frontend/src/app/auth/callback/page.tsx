"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { useAuth } from "@/features/auth/auth-provider";
import { exchangeOAuthCode } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { consumeOAuthFlow, sanitizeAppPath } from "@/lib/auth/oauth";

function CallbackInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { applyEstablishedSession } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        // 1. Explicitly reject implicit flow tokens in hash
        const hash = typeof window !== "undefined" ? window.location.hash.replace(/^#/, "") : "";
        if (hash.includes("access_token") || hash.includes("token=")) {
          window.history.replaceState({}, "", "/auth/callback");
          throw new Error(
            "Implicit token flow is not supported. Please sign in again using secure sign-in.",
          );
        }

        // 2. Check for provider-reported errors
        const errorParam = searchParams.get("error");
        const errorDescription = searchParams.get("error_description");
        if (errorParam) {
          window.history.replaceState({}, "", "/auth/callback");
          if (errorParam === "access_denied") {
            throw new Error("Google sign-in was cancelled. Please try again.");
          }
          throw new Error(
            errorDescription ||
              "Google sign-in is currently unavailable. Please try again or use another login method.",
          );
        }

        // 3. Inspect authorization code
        const code = searchParams.get("code");
        const state = searchParams.get("state");

        if (!code) {
          window.history.replaceState({}, "", "/auth/callback");
          throw new Error("Authorization code is missing. Please start sign-in again.");
        }

        // 4. Consume origin-bound OAuth flow record (single-use, validated, and expired check)
        const flow = consumeOAuthFlow(state);
        if (!flow) {
          window.history.replaceState({}, "", "/auth/callback");
          throw new Error(
            "Sign-in session expired, was invalid, or was already completed. Please start sign-in again.",
          );
        }

        // 5. Remove credentials from the address bar immediately before network operations
        window.history.replaceState({}, "", "/auth/callback");

        // 6. Complete PKCE code exchange with backend
        const backend = await exchangeOAuthCode({
          code,
          code_verifier: flow.codeVerifier,
        });

        if (!backend.session?.authenticated) {
          throw new Error(backend.message || "Failed to establish authenticated session");
        }

        // 7. Apply the BFF-managed HttpOnly cookie session and redirect
        await applyEstablishedSession();

        if (!cancelled) {
          const destination = sanitizeAppPath(flow.next);
          router.replace(destination);
          router.refresh();
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? err.message
              : err instanceof Error
                ? err.message
                : "Authentication callback failed",
          );
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [applyEstablishedSession, router, searchParams]);

  if (error) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center gap-4 px-6 py-16 text-center">
        <div className="max-w-md space-y-2">
          <h1 className="text-lg font-semibold tracking-tight text-foreground">Sign-in failed</h1>
          <p className="text-sm text-muted-foreground">{error}</p>
        </div>
        <Link
          href="/login"
          className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90"
        >
          Back to sign in
        </Link>
      </main>
    );
  }

  return (
    <main className="flex flex-1 items-center justify-center px-6 py-16">
      <p className="text-sm text-muted-foreground">Completing secure sign-in…</p>
    </main>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <main className="flex flex-1 items-center justify-center px-6 py-16">
          <p className="text-sm text-muted-foreground">Completing secure sign-in…</p>
        </main>
      }
    >
      <CallbackInner />
    </Suspense>
  );
}
