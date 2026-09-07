/**
 * Google OAuth PKCE parameters, state management, and safe destination sanitization.
 */

export type OAuthFlowRecord = {
  state: string;
  codeVerifier: string;
  next: string;
  createdAt: number;
};

const STATE_COOKIE_PREFIX = "fb_oauth_";
const STATE_STORAGE_PREFIX = "fb_oauth_";
const MAX_STATE_AGE_MS = 10 * 60 * 1000; // 10 minutes

/**
 * Validate that destination is a safe, same-origin relative app path.
 * Rejects external URLs, protocol-relative URLs (//), backslashes, fragments (#),
 * path traversal (/../ or %2e%2e), control characters, and non-app paths.
 * Always falls back safely to '/app'.
 */
export function sanitizeAppPath(destination: string | null | undefined): string {
  if (!destination || typeof destination !== "string") {
    return "/app";
  }

  const clean = destination.trim();
  if (!clean) {
    return "/app";
  }

  // Reject protocol-relative, backslashes, or fragments
  if (clean.startsWith("//") || clean.includes("\\") || clean.includes("#")) {
    return "/app";
  }

  // Reject control characters or CRLF
  for (let i = 0; i < clean.length; i++) {
    const code = clean.charCodeAt(i);
    if (code < 32 || code === 127) {
      return "/app";
    }
  }

  // Must start with single /
  if (!clean.startsWith("/")) {
    return "/app";
  }

  // Check traversal in raw clean string before URL normalization
  if (clean.split("/").some((s) => s === ".." || s === ".")) {
    return "/app";
  }

  try {
    const decodedClean = decodeURIComponent(clean);
    if (decodedClean.split("/").some((s) => s === ".." || s === ".")) {
      return "/app";
    }
  } catch {
    return "/app";
  }

  try {
    // Parse using dummy base to inspect components safely
    const parsed = new URL(clean, "http://localhost");

    // Must have same host and scheme as dummy base (rejects any scheme smuggling)
    if (parsed.origin !== "http://localhost") {
      return "/app";
    }

    const path = parsed.pathname;

    // Check traversal in both raw and decoded path
    try {
      const decoded = decodeURIComponent(path);
      const decodedSegments = decoded.split("/").filter(Boolean);
      if (decodedSegments.some((s) => s === ".." || s === ".")) {
        return "/app";
      }
    } catch {
      return "/app";
    }

    const segments = path.split("/").filter(Boolean);
    if (segments.some((s) => s === ".." || s === ".")) {
      return "/app";
    }

    // Must be /app or /app/...
    if (path !== "/app" && !path.startsWith("/app/")) {
      return "/app";
    }

    return `${path}${parsed.search}`;
  } catch {
    return "/app";
  }
}

// In-memory fallback for test runners and headless environments
const inMemoryStore = new Map<string, string>();

function bufferToBase64Url(buffer: ArrayBuffer | Uint8Array): string {
  const bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/**
 * Generate a cryptographically secure random base64url string.
 */
export function generateRandomString(bytesCount = 32): string {
  const array = new Uint8Array(bytesCount);
  globalThis.crypto.getRandomValues(array);
  return bufferToBase64Url(array);
}

/**
 * Generate PKCE code_verifier and code_challenge (S256).
 */
export async function generatePKCEPair(): Promise<{
  codeVerifier: string;
  codeChallenge: string;
}> {
  const codeVerifier = generateRandomString(32); // 43 chars urlsafe
  const encoder = new TextEncoder();
  const data = encoder.encode(codeVerifier);
  const digest = await globalThis.crypto.subtle.digest("SHA-256", data);
  const codeChallenge = bufferToBase64Url(digest);
  return { codeVerifier, codeChallenge };
}

/**
 * Generate a random state string bound to the intended next path.
 */
export function generateOAuthState(): string {
  return generateRandomString(24);
}

function setCookie(name: string, value: string, maxAgeSeconds: number): void {
  if (typeof document === "undefined") return;
  const isSecure = window.location.protocol === "https:";
  document.cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}; Path=/auth/callback; SameSite=Lax; Max-Age=${maxAgeSeconds}${isSecure ? "; Secure" : ""}`;
}

function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie
    .split(";")
    .map((c) => c.trim())
    .find((c) => c.startsWith(`${encodeURIComponent(name)}=`));
  if (!match) return null;
  const rawValue = match.substring(encodeURIComponent(name).length + 1);
  return decodeURIComponent(rawValue);
}

function deleteCookie(name: string): void {
  if (typeof document === "undefined") return;
  document.cookie = `${encodeURIComponent(name)}=; Path=/auth/callback; SameSite=Lax; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT`;
}

export function storeOAuthFlow(record: OAuthFlowRecord): void {
  const payload = JSON.stringify(record);

  // 1. Store in sessionStorage (per-tab storage)
  if (typeof window !== "undefined" && window.sessionStorage) {
    try {
      window.sessionStorage.setItem(`${STATE_STORAGE_PREFIX}${record.state}`, payload);
    } catch {
      // Quota or private mode fallback
    }
  }

  // 2. Store in cookie (works across tab transitions if needed, 10 min expiry)
  setCookie(`${STATE_COOKIE_PREFIX}${record.state}`, payload, 600);

  // 3. Store in memory fallback (for test runners / headless runtime)
  inMemoryStore.set(`${STATE_STORAGE_PREFIX}${record.state}`, payload);
}

/**
 * Retrieve and immediately delete (consume) the stored OAuth flow state.
 * Returns null if missing, expired, or invalid.
 */
export function consumeOAuthFlow(state: string | null | undefined): OAuthFlowRecord | null {
  if (!state || typeof state !== "string") return null;

  let raw: string | null = null;
  const storageKey = `${STATE_STORAGE_PREFIX}${state}`;
  const cookieKey = `${STATE_COOKIE_PREFIX}${state}`;

  // 1. Try sessionStorage first
  if (typeof window !== "undefined" && window.sessionStorage) {
    try {
      raw = window.sessionStorage.getItem(storageKey);
      window.sessionStorage.removeItem(storageKey);
    } catch {
      // Session storage unavailable
    }
  }

  // 2. Check cookie if not in sessionStorage
  if (!raw) {
    raw = getCookie(cookieKey);
  }

  // 3. Check memory fallback if not in cookie/sessionStorage
  if (!raw) {
    raw = inMemoryStore.get(storageKey) ?? null;
  }

  // Always delete from all storage mechanisms
  deleteCookie(cookieKey);
  inMemoryStore.delete(storageKey);

  if (!raw) return null;

  try {
    const record = JSON.parse(raw) as OAuthFlowRecord;
    if (typeof record !== "object" || record === null) return null;
    if (record.state !== state) return null;
    if (typeof record.codeVerifier !== "string" || !record.codeVerifier) return null;
    if (typeof record.createdAt !== "number") return null;

    // Verify age (max 10 minutes)
    if (Date.now() - record.createdAt > MAX_STATE_AGE_MS) {
      return null;
    }

    // Re-sanitize next destination
    record.next = sanitizeAppPath(record.next);

    return record;
  } catch {
    return null;
  }
}
