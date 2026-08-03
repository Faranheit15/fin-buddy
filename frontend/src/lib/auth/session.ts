/**
 * Frontend session cookies (set via Next.js route handlers on this origin).
 * Auth credentials themselves are obtained only from the FastAPI backend.
 */

export const ACCESS_COOKIE = "fb_access_token";
export const REFRESH_COOKIE = "fb_refresh_token";
export const EXPIRES_COOKIE = "fb_expires_at";

export type StoredSession = {
  accessToken: string;
  refreshToken: string | null;
  expiresAt: number | null;
};

export type BackendTokenPair = {
  access_token?: string | null;
  refresh_token?: string | null;
  expires_in?: number | null;
  expires_at?: number | null;
  token_type?: string;
};

export function tokensFromBackendSession(
  session: BackendTokenPair | null | undefined,
): StoredSession | null {
  if (!session?.access_token) return null;
  let expiresAt = session.expires_at ?? null;
  if (!expiresAt && session.expires_in) {
    expiresAt = Math.floor(Date.now() / 1000) + session.expires_in;
  }
  return {
    accessToken: session.access_token,
    refreshToken: session.refresh_token ?? null,
    expiresAt,
  };
}
