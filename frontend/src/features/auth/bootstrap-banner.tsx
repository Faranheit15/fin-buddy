"use client";

import { useAuth } from "@/features/auth/auth-provider";

/**
 * Shows workspace bootstrap status after login when profile is loaded from the API.
 */
export function BootstrapBanner() {
  const { ready, profile, organizations } = useAuth();

  if (!ready) return null;

  if (!profile) {
    return (
      <div className="mb-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-900 dark:text-amber-100">
        Session cookie present, but <code className="font-mono">GET /api/v1/auth/me</code> failed.
        Confirm the FastAPI backend is running and Supabase JWT + database credentials are set in{" "}
        <code className="font-mono">backend/.env</code>.
      </div>
    );
  }

  if (organizations.length === 0) {
    return (
      <div className="mb-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs">
        Profile exists but no organization membership was returned.
      </div>
    );
  }

  return null;
}
