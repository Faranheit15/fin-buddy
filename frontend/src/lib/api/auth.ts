import { apiFetch } from "@/lib/api/client";
import type { BackendTokenPair } from "@/lib/auth/session";
import { env } from "@/lib/env";

export type ProfileResponse = {
  id: string;
  email: string | null;
  phone: string | null;
  display_name: string | null;
  avatar_url: string | null;
  timezone: string;
  due_soon_days: number;
  high_utilization_percent: number;
  email_reminders_enabled: boolean;
  platform_role: "user" | "admin" | "super_admin";
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
};

export type ProfileUpdate = {
  display_name?: string | null;
  timezone?: string;
  due_soon_days?: number;
  high_utilization_percent?: number;
  email_reminders_enabled?: boolean;
};

export type OrganizationSummary = {
  id: string;
  name: string;
  slug: string;
  role: "owner" | "admin" | "member";
};

export type MeResponse = {
  user: ProfileResponse;
  organizations: OrganizationSummary[];
};

export type AuthResponse = {
  user: ProfileResponse | null;
  organization: OrganizationSummary | null;
  session: BackendTokenPair | null;
  message: string | null;
  raw?: Record<string, unknown> | null;
};

export function loginWithPassword(email: string, password: string) {
  return apiFetch<AuthResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

/** Development demo login — no Supabase email. */
export function demoLogin() {
  return apiFetch<AuthResponse>("/api/v1/auth/demo-login", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function signupWithPassword(
  email: string,
  password: string,
  display_name?: string,
) {
  return apiFetch<AuthResponse>("/api/v1/auth/signup", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
      display_name: display_name || null,
      redirect_to: `${env.NEXT_PUBLIC_APP_URL}/auth/callback`,
    }),
  });
}

export function requestMagicLink(email: string, redirectTo?: string) {
  return apiFetch<{ message: string }>("/api/v1/auth/magic-link", {
    method: "POST",
    body: JSON.stringify({
      email,
      redirect_to: redirectTo ?? `${env.NEXT_PUBLIC_APP_URL}/auth/callback`,
    }),
  });
}

export function verifyOtp(input: {
  email?: string;
  phone?: string;
  token: string;
  type?: string;
}) {
  return apiFetch<AuthResponse>("/api/v1/auth/otp/verify", {
    method: "POST",
    body: JSON.stringify({
      email: input.email ?? null,
      phone: input.phone ?? null,
      token: input.token,
      type: input.type ?? "email",
    }),
  });
}

export function refreshSession(refreshToken: string) {
  return apiFetch<AuthResponse>("/api/v1/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function establishSessionFromTokens(session: BackendTokenPair) {
  return apiFetch<AuthResponse>("/api/v1/auth/session", {
    method: "POST",
    body: JSON.stringify({
      access_token: session.access_token,
      refresh_token: session.refresh_token ?? null,
      expires_in: session.expires_in ?? null,
      expires_at: session.expires_at ?? null,
    }),
  });
}

export function getGoogleOAuthUrl(redirectTo: string) {
  const q = new URLSearchParams({ redirect_to: redirectTo });
  return apiFetch<{ url: string; note: string }>(
    `/api/v1/auth/oauth/google?${q.toString()}`,
    { method: "GET" },
  );
}

export function fetchMe(accessToken: string, signal?: AbortSignal) {
  return apiFetch<MeResponse>(
    "/api/v1/auth/me",
    { method: "GET" },
    { accessToken, signal },
  );
}

export function updateProfile(accessToken: string, body: ProfileUpdate) {
  return apiFetch<ProfileResponse>(
    "/api/v1/auth/me",
    { method: "PATCH", body: JSON.stringify(body) },
    { accessToken },
  );
}

export function updateOrganization(
  accessToken: string,
  orgId: string,
  body: { name: string },
) {
  return apiFetch<OrganizationSummary>(
    `/api/v1/auth/organizations/${orgId}`,
    { method: "PATCH", body: JSON.stringify(body) },
    { accessToken },
  );
}

export function logoutApi(accessToken: string) {
  return apiFetch<{ message: string }>(
    "/api/v1/auth/logout",
    { method: "POST" },
    { accessToken },
  );
}

/** Persist tokens on the Next.js origin (httpOnly cookies). */
export async function persistBrowserSession(session: {
  accessToken: string;
  refreshToken: string | null;
  expiresAt: number | null;
}) {
  const res = await fetch("/api/auth/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(session),
  });
  if (!res.ok) {
    throw new Error("Failed to persist session");
  }
}

export async function clearBrowserSession() {
  await fetch("/api/auth/session", { method: "DELETE" });
}

export async function readBrowserSession(): Promise<{
  accessToken: string;
  refreshToken: string | null;
  expiresAt: number | null;
} | null> {
  const res = await fetch("/api/auth/session", { method: "GET", cache: "no-store" });
  if (!res.ok) return null;
  const data = (await res.json()) as {
    session: {
      accessToken: string;
      refreshToken: string | null;
      expiresAt: number | null;
    } | null;
  };
  return data.session;
}
