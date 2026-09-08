import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import {
  ACCESS_COOKIE,
  EXPIRES_COOKIE,
  REFRESH_COOKIE,
  sessionCookieOptions,
  type BackendTokenPair,
} from "@/lib/auth/session";

export const dynamic = "force-dynamic";

const BACKEND_URL = (process.env.BACKEND_URL || "http://127.0.0.1:8001").replace(/\/$/, "");

const NO_STORE_HEADERS = {
  "Cache-Control": "no-store, private",
  Pragma: "no-cache",
  Vary: "Cookie",
};

const AUTH_SESSION_PATHS = new Set([
  "/api/v1/auth/login",
  "/api/v1/auth/demo-login",
  "/api/v1/auth/otp/verify",
  "/api/v1/auth/session",
  "/api/v1/auth/refresh",
  "/api/v1/auth/signup",
]);

const STRIPPED_REQUEST_HEADERS = [
  "authorization",
  "connection",
  "content-length",
  "cookie",
  "host",
  "origin",
  "referer",
  "x-forwarded-for",
  "x-forwarded-host",
  "x-forwarded-proto",
  "x-job-secret",
];

type BackendAuthResponse = {
  session?: BackendTokenPair | null;
  raw?: unknown;
  [key: string]: unknown;
};

type SanitizedAuthResponse = Omit<BackendAuthResponse, "raw" | "session"> & {
  session: { authenticated: true } | null;
};

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

function isSameOriginRequest(request: Request): boolean {
  const origin = request.headers.get("origin");
  if (!origin) return request.method === "GET" || request.method === "HEAD";
  try {
    return new URL(origin).origin === new URL(request.url).origin;
  } catch {
    return false;
  }
}

function forbiddenResponse() {
  return NextResponse.json(
    { error: "Cross-site API requests are not allowed" },
    { status: 403, headers: NO_STORE_HEADERS },
  );
}

function backendRequestHeaders(request: Request, accessToken: string | null): Headers {
  const headers = new Headers(request.headers);
  for (const header of STRIPPED_REQUEST_HEADERS) headers.delete(header);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  return headers;
}

function backendResponseHeaders(response: Response): Headers {
  const headers = new Headers(NO_STORE_HEADERS);
  for (const name of [
    "content-disposition",
    "content-type",
    "etag",
    "x-request-id",
    "idempotency-key",
    "idempotency-replayed",
  ]) {
    const value = response.headers.get(name);
    if (value) headers.set(name, value);
  }
  return headers;
}

function tokenExpiry(token: BackendTokenPair): number | null {
  if (typeof token.expires_at === "number") return token.expires_at;
  if (typeof token.expires_in === "number") return Math.floor(Date.now() / 1000) + token.expires_in;
  return null;
}

function storeSession(token: BackendTokenPair, jar: Awaited<ReturnType<typeof cookies>>) {
  if (!token.access_token) return false;

  const expiresAt = tokenExpiry(token);
  const maxAge = expiresAt ? Math.max(expiresAt - Math.floor(Date.now() / 1000), 60) : 60 * 60;
  const cookieOptions = sessionCookieOptions();
  jar.set(ACCESS_COOKIE, token.access_token, { ...cookieOptions, maxAge });
  if (token.refresh_token) {
    jar.set(REFRESH_COOKIE, token.refresh_token, { ...cookieOptions, maxAge: 60 * 60 * 24 * 30 });
  } else {
    jar.delete(REFRESH_COOKIE);
  }
  if (expiresAt) {
    jar.set(EXPIRES_COOKIE, String(expiresAt), { ...cookieOptions, maxAge });
  } else {
    jar.delete(EXPIRES_COOKIE);
  }
  return true;
}

function clearSession(jar: Awaited<ReturnType<typeof cookies>>) {
  jar.delete(ACCESS_COOKIE);
  jar.delete(REFRESH_COOKIE);
  jar.delete(EXPIRES_COOKIE);
}

async function refreshAccessToken(
  jar: Awaited<ReturnType<typeof cookies>>,
  refreshToken: string,
): Promise<string | null> {
  const response = await fetch(`${BACKEND_URL}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
    cache: "no-store",
  });
  if (!response.ok) {
    clearSession(jar);
    return null;
  }

  const data = (await response.json()) as BackendAuthResponse;
  if (!data.session?.access_token || !storeSession(data.session, jar)) {
    clearSession(jar);
    return null;
  }
  return data.session.access_token;
}

async function authenticatedAccessToken(jar: Awaited<ReturnType<typeof cookies>>) {
  const accessToken = jar.get(ACCESS_COOKIE)?.value ?? null;
  const refreshToken = jar.get(REFRESH_COOKIE)?.value ?? null;
  const expiresAt = Number(jar.get(EXPIRES_COOKIE)?.value ?? "");
  const shouldRefresh =
    refreshToken &&
    (!accessToken || !Number.isFinite(expiresAt) || expiresAt < Date.now() / 1000 + 60);
  if (shouldRefresh) return refreshAccessToken(jar, refreshToken);
  return accessToken;
}

function sanitizedAuthResponse(
  data: BackendAuthResponse,
  sessionStored: boolean,
): SanitizedAuthResponse {
  const safe = Object.fromEntries(
    Object.entries(data).filter(([key]) => key !== "raw" && key !== "session"),
  );
  return { ...safe, session: sessionStored ? { authenticated: true } : null };
}

async function handle(request: Request, context: RouteContext) {
  if (!isSameOriginRequest(request)) return forbiddenResponse();

  const { path: segments } = await context.params;
  const path = `/${segments.join("/")}`;
  if (!path.startsWith("/api/v1/") || path.includes("..")) {
    return NextResponse.json(
      { error: "Invalid backend path" },
      { status: 400, headers: NO_STORE_HEADERS },
    );
  }

  const jar = await cookies();
  const isLogout = path === "/api/v1/auth/logout";
  const isRefresh = path === "/api/v1/auth/refresh";
  const accessToken = isRefresh
    ? await authenticatedAccessToken(jar)
    : isLogout
      ? (jar.get(ACCESS_COOKIE)?.value ?? null)
      : await authenticatedAccessToken(jar);

  if (isRefresh) {
    if (!accessToken) {
      return NextResponse.json({ session: null }, { status: 401, headers: NO_STORE_HEADERS });
    }
    return NextResponse.json({ session: { authenticated: true } }, { headers: NO_STORE_HEADERS });
  }

  const upstream = await fetch(`${BACKEND_URL}${path}${new URL(request.url).search}`, {
    method: request.method,
    headers: backendRequestHeaders(request, accessToken),
    body: request.method === "GET" || request.method === "HEAD" ? undefined : request.body,
    cache: "no-store",
    // Required by Node's fetch implementation when a request stream is forwarded.
    duplex: "half",
  } as RequestInit);

  if (isLogout) clearSession(jar);

  const headers = backendResponseHeaders(upstream);
  if (
    !AUTH_SESSION_PATHS.has(path) ||
    !upstream.headers.get("content-type")?.includes("application/json")
  ) {
    return new NextResponse(upstream.body, { status: upstream.status, headers });
  }

  const data = (await upstream.json()) as BackendAuthResponse;
  const sessionStored = Boolean(data.session?.access_token && storeSession(data.session, jar));
  return NextResponse.json(sanitizedAuthResponse(data, sessionStored), {
    status: upstream.status,
    headers,
  });
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
