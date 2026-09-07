import { apiFetch } from "@/lib/api/client";
import type { BrowserSession } from "@/lib/auth/session";
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

/** Browser-visible form of an auth response; credentials are never included. */
export type AuthResponse = {
  user: ProfileResponse | null;
  organization: OrganizationSummary | null;
  session: { authenticated: true } | null;
  message: string | null;
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

export function signupWithPassword(email: string, password: string, displayName?: string) {
  return apiFetch<AuthResponse>("/api/v1/auth/signup", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
      display_name: displayName || null,
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

export function verifyOtp(input: { email?: string; phone?: string; token: string; type?: string }) {
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

/** Complete PKCE OAuth code exchange without exposing credentials in the response. */
export function exchangeOAuthCode(payload: { code: string; code_verifier: string }) {
  return apiFetch<AuthResponse>("/api/v1/auth/session", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** Complete an OAuth or magic-link return without exposing backend credentials in the response. */
export function establishSessionFromTokens(session: {
  access_token: string;
  refresh_token?: string | null;
  expires_in?: number | null;
  expires_at?: number | null;
}) {
  return apiFetch<AuthResponse>("/api/v1/auth/session", {
    method: "POST",
    body: JSON.stringify(session),
  });
}

export function getGoogleOAuthUrl(
  options?:
    | {
        redirectTo?: string;
        codeChallenge?: string;
        state?: string;
      }
    | string,
) {
  const params = new URLSearchParams();
  if (typeof options === "string") {
    params.set("redirect_to", options);
  } else if (options) {
    if (options.redirectTo) params.set("redirect_to", options.redirectTo);
    if (options.codeChallenge) {
      params.set("code_challenge", options.codeChallenge);
      params.set("code_challenge_method", "s256");
    }
    if (options.state) params.set("state", options.state);
  }
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiFetch<{ url: string; note: string }>(`/api/v1/auth/oauth/google${query}`, {
    method: "GET",
  });
}

export function fetchMe(accessToken: string, signal?: AbortSignal) {
  return apiFetch<MeResponse>("/api/v1/auth/me", { method: "GET" }, { accessToken, signal });
}

export function updateProfile(accessToken: string, body: ProfileUpdate) {
  return apiFetch<ProfileResponse>(
    "/api/v1/auth/me",
    { method: "PATCH", body: JSON.stringify(body) },
    { accessToken },
  );
}

export function updateOrganization(accessToken: string, orgId: string, body: { name: string }) {
  return apiFetch<OrganizationSummary>(
    `/api/v1/auth/organizations/${orgId}`,
    { method: "PATCH", body: JSON.stringify(body) },
    { accessToken },
  );
}

export function logoutApi(accessToken: string) {
  return apiFetch<{ message: string }>("/api/v1/auth/logout", { method: "POST" }, { accessToken });
}

export async function clearBrowserSession() {
  await fetch("/api/auth/session", { method: "DELETE" });
}

export async function readBrowserSession(): Promise<BrowserSession | null> {
  const res = await fetch("/api/auth/session", { method: "GET", cache: "no-store" });
  if (!res.ok) return null;
  const data = (await res.json()) as { session: BrowserSession | null };
  return data.session;
}
