/**
 * Session cookie names and non-secret browser session metadata.
 * Credentials are read only by Next.js route handlers.
 */

const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "";
const useSecureCookies = process.env.NODE_ENV === "production" || appUrl.startsWith("https://");

export const ACCESS_COOKIE = "fb_access_token";
export const REFRESH_COOKIE = "fb_refresh_token";
export const EXPIRES_COOKIE = "fb_expires_at";

/** A non-secret UI marker retained while API call sites migrate to BFF-only signatures. */
export const BFF_SESSION_MARKER = "bff-session";

export type BrowserSession = {
  authenticated: true;
  expiresAt: number | null;
};

export type BackendTokenPair = {
  access_token?: string | null;
  refresh_token?: string | null;
  expires_in?: number | null;
  expires_at?: number | null;
  token_type?: string;
};

export function sessionCookieOptions() {
  return {
    httpOnly: true,
    sameSite: "strict" as const,
    secure: useSecureCookies,
    path: "/",
  };
}
