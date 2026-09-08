import { env } from "@/lib/env";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
    readonly details?: unknown,
    readonly requestId?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export type ApiClientOptions = {
  accessToken?: string | null;
  signal?: AbortSignal;
  idempotencyKey?: string;
};

type ErrorBody = {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
};

/**
 * Resolve API base URL.
 * - In the browser: use the same-origin Next.js BFF, which owns credentials.
 * - On the server: call the configured backend directly.
 */
export function apiBase(): string {
  if (typeof window !== "undefined") {
    return "/api/backend";
  }
  return env.BACKEND_URL.replace(/\/$/, "");
}

/**
 * Thin fetch wrapper for the FastAPI backend.
 */
export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  options: ApiClientOptions = {},
): Promise<T> {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  const url = path.startsWith("http") ? path : `${apiBase()}${normalized}`;

  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  if (options.idempotencyKey) {
    headers.set("Idempotency-Key", options.idempotencyKey);
  }
  if (options.accessToken && typeof window === "undefined") {
    headers.set("Authorization", `Bearer ${options.accessToken}`);
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers,
      signal: options.signal ?? init.signal,
    });
  } catch (err) {
    const hint =
      typeof window !== "undefined"
        ? "Is the Fin Buddy API running, and is the Next.js BFF route able to reach the configured backend?"
        : "Is the Fin Buddy API reachable from the Next.js server?";
    const detail = err instanceof Error ? err.message : "network error";
    throw new ApiError(`Failed to reach API (${url}): ${detail}. ${hint}`, 0, "network_error");
  }

  if (!response.ok) {
    let code: string | undefined;
    let message = response.statusText || "Request failed";
    let details: unknown;

    try {
      const body = (await response.json()) as ErrorBody;
      code = body.error?.code;
      message = body.error?.message ?? message;
      details = body.error?.details;
    } catch {
      // non-JSON error body
    }

    throw new ApiError(
      message,
      response.status,
      code,
      details,
      response.headers.get("x-request-id") ?? undefined,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export type HealthResponse = {
  status: "ok" | "degraded" | "error";
  app: string;
  version: string;
  environment: string;
};

export function getApiHealth(signal?: AbortSignal) {
  return apiFetch<HealthResponse>("/api/v1/health", { method: "GET" }, { signal });
}
