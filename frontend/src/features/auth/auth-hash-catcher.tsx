"use client";

import { useEffect } from "react";

/**
 * Supabase falls back to Site URL (often `/`) when `email_redirect_to` is
 * missing or not allow-listed. Tokens then sit in the hash with no handler.
 * Forward them to `/auth/callback`, which completes the backend session.
 */
export function AuthHashCatcher() {
  useEffect(() => {
    if (typeof window === "undefined") return;

    const { pathname, hash, search } = window.location;
    if (pathname.startsWith("/auth/callback")) return;
    if (!hash || !hash.includes("access_token=")) return;

    window.location.replace(`/auth/callback${search}${hash}`);
  }, []);

  return null;
}
