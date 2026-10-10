import { afterEach, beforeEach, describe, expect, mock, test } from "bun:test";
import {
  GET,
  MAX_ATTEMPTS,
  RETRY_BACKOFF_MS,
  UPSTREAM_TIMEOUT_MS,
  dynamic,
  maxDuration,
  runtime,
} from "./route";

const originalFetch = globalThis.fetch;

describe("GET /api/cron/supabase-keepalive configuration", () => {
  test("exports route segment configuration covering cold starts", () => {
    expect(dynamic).toBe("force-dynamic");
    expect(runtime).toBe("nodejs");
    expect(maxDuration).toBe(60);
    expect(UPSTREAM_TIMEOUT_MS).toBe(25_000);
    expect(RETRY_BACKOFF_MS).toBe(1_000);
    expect(MAX_ATTEMPTS).toBe(2);
    // maxDuration (seconds) must safely exceed upstream timeout (seconds)
    expect(maxDuration).toBeGreaterThanOrEqual(30);
    expect(maxDuration).toBeGreaterThan(UPSTREAM_TIMEOUT_MS / 1000);
  });
});

describe("GET /api/cron/supabase-keepalive", () => {
  const originalCronSecret = process.env.CRON_SECRET;
  const originalBackendUrl = process.env.BACKEND_URL;
  const originalEnableFlag = process.env.ENABLE_KEEPALIVE_CRON;

  beforeEach(() => {
    // Keep mock secret under 24 chars to avoid triggering repo secret scanning regex
    process.env.CRON_SECRET = "mock-secret-1234";
    process.env.BACKEND_URL = "http://127.0.0.1:8001";
    delete process.env.ENABLE_KEEPALIVE_CRON;
  });

  afterEach(() => {
    process.env.CRON_SECRET = originalCronSecret;
    process.env.BACKEND_URL = originalBackendUrl;
    process.env.ENABLE_KEEPALIVE_CRON = originalEnableFlag;
    globalThis.fetch = originalFetch;
  });

  test("returns 200 and disabled message when ENABLE_KEEPALIVE_CRON is false", async () => {
    process.env.ENABLE_KEEPALIVE_CRON = "false";
    const req = new Request("http://localhost:3000/api/cron/supabase-keepalive");
    const res = await GET(req);
    expect(res.status).toBe(200);
    const body = (await res.json()) as { ok: boolean; message: string };
    expect(body.ok).toBe(false);
    expect(body.message).toBe("Keepalive cron is disabled");
  });

  test("returns 503 when CRON_SECRET is not configured", async () => {
    delete process.env.CRON_SECRET;
    const req = new Request("http://localhost:3000/api/cron/supabase-keepalive", {
      headers: { authorization: "Bearer mock-secret-1234" },
    });
    const res = await GET(req);
    expect(res.status).toBe(503);
    const body = (await res.json()) as { ok: boolean; error: string };
    expect(body.ok).toBe(false);
    expect(body.error).toBe("CRON_SECRET is not configured");
  });

  test("returns 401 when authorization header is missing", async () => {
    const req = new Request("http://localhost:3000/api/cron/supabase-keepalive");
    const res = await GET(req);
    expect(res.status).toBe(401);
    const body = (await res.json()) as { ok: boolean; error: string };
    expect(body.ok).toBe(false);
    expect(body.error).toBe("Unauthorized");
  });

  test("returns 401 when authorization scheme is not Bearer", async () => {
    const req = new Request("http://localhost:3000/api/cron/supabase-keepalive", {
      headers: { authorization: "Basic dXNlcjpwYXNz" },
    });
    const res = await GET(req);
    expect(res.status).toBe(401);
  });

  test("returns 401 when bearer token does not match secret", async () => {
    const req = new Request("http://localhost:3000/api/cron/supabase-keepalive", {
      headers: { authorization: "Bearer wrong-secret" },
    });
    const res = await GET(req);
    expect(res.status).toBe(401);
  });

  test("proxies upstream /ready with cache: no-store and returns 200 on success without retrying", async () => {
    let capturedUrl = "";
    let capturedInit: RequestInit | undefined;
    let callCount = 0;

    globalThis.fetch = mock(async (input: RequestInfo | URL, init?: RequestInit) => {
      callCount++;
      capturedUrl = String(input);
      capturedInit = init;
      return new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }) as unknown as typeof fetch;

    const req = new Request("http://localhost:3000/api/cron/supabase-keepalive", {
      headers: { authorization: "Bearer mock-secret-1234" },
    });

    const res = await GET(req);
    expect(res.status).toBe(200);
    const body = (await res.json()) as {
      ok: boolean;
      status: string;
      requestId: string;
      attempts: number;
    };
    expect(body.ok).toBe(true);
    expect(body.status).toBe("ok");
    expect(body.requestId).toMatch(/^cron-keepalive-/);
    expect(body.attempts).toBe(1);
    expect(callCount).toBe(1);

    expect(capturedUrl).toBe("http://127.0.0.1:8001/api/v1/ready");
    expect(capturedInit?.cache).toBe("no-store");
    const headers = capturedInit?.headers as Record<string, string>;
    expect(headers?.["User-Agent"]).toBe("fin-buddy-cron/1.0");
    expect(headers?.["X-Request-Id"]).toBe(body.requestId);
    expect(headers?.["Cookie"]).toBeUndefined();
  });

  test("retries once and succeeds when initial request fails with network error or timeout", async () => {
    let callCount = 0;

    globalThis.fetch = mock(async () => {
      callCount++;
      if (callCount === 1) {
        throw new Error("Connection timeout during container cold start");
      }
      return new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }) as unknown as typeof fetch;

    const req = new Request("http://localhost:3000/api/cron/supabase-keepalive", {
      headers: { authorization: "Bearer mock-secret-1234" },
    });

    const res = await GET(req);
    expect(res.status).toBe(200);
    const body = (await res.json()) as { ok: boolean; status: string; attempts: number };
    expect(body.ok).toBe(true);
    expect(body.status).toBe("ok");
    expect(body.attempts).toBe(2);
    expect(callCount).toBe(2);
  });

  test("retries once and succeeds when initial request returns 5xx error", async () => {
    let callCount = 0;

    globalThis.fetch = mock(async () => {
      callCount++;
      if (callCount === 1) {
        return new Response(JSON.stringify({ status: "degraded" }), {
          status: 503,
          headers: { "content-type": "application/json" },
        });
      }
      return new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }) as unknown as typeof fetch;

    const req = new Request("http://localhost:3000/api/cron/supabase-keepalive", {
      headers: { authorization: "Bearer mock-secret-1234" },
    });

    const res = await GET(req);
    expect(res.status).toBe(200);
    const body = (await res.json()) as { ok: boolean; status: string; attempts: number };
    expect(body.ok).toBe(true);
    expect(body.status).toBe("ok");
    expect(body.attempts).toBe(2);
    expect(callCount).toBe(2);
  });

  test("does not retry on 4xx client errors and returns 503 degraded immediately", async () => {
    let callCount = 0;

    globalThis.fetch = mock(async () => {
      callCount++;
      return new Response(JSON.stringify({ detail: "Not found" }), {
        status: 404,
        headers: { "content-type": "application/json" },
      });
    }) as unknown as typeof fetch;

    const req = new Request("http://localhost:3000/api/cron/supabase-keepalive", {
      headers: { authorization: "Bearer mock-secret-1234" },
    });

    const res = await GET(req);
    expect(res.status).toBe(503);
    const body = (await res.json()) as {
      ok: boolean;
      status: string;
      upstreamStatus: number;
      attempts: number;
    };
    expect(body.ok).toBe(false);
    expect(body.status).toBe("degraded");
    expect(body.upstreamStatus).toBe(404);
    expect(body.attempts).toBe(1);
    expect(callCount).toBe(1);
  });

  test("returns 503 degraded after retrying once when 5xx persists", async () => {
    let callCount = 0;

    globalThis.fetch = mock(async () => {
      callCount++;
      return new Response(JSON.stringify({ status: "degraded" }), {
        status: 503,
        headers: { "content-type": "application/json" },
      });
    }) as unknown as typeof fetch;

    const req = new Request("http://localhost:3000/api/cron/supabase-keepalive", {
      headers: { authorization: "Bearer mock-secret-1234" },
    });

    const res = await GET(req);
    expect(res.status).toBe(503);
    const body = (await res.json()) as {
      ok: boolean;
      status: string;
      upstreamStatus: number;
      attempts: number;
    };
    expect(body.ok).toBe(false);
    expect(body.status).toBe("degraded");
    expect(body.upstreamStatus).toBe(503);
    expect(body.attempts).toBe(2);
    expect(callCount).toBe(2);
  });

  test("returns 504 error after retrying once when upstream request persistently times out or fails", async () => {
    let callCount = 0;

    globalThis.fetch = mock(async () => {
      callCount++;
      throw new Error("Connection timed out after 25s");
    }) as unknown as typeof fetch;

    const req = new Request("http://localhost:3000/api/cron/supabase-keepalive", {
      headers: { authorization: "Bearer mock-secret-1234" },
    });

    const res = await GET(req);
    expect(res.status).toBe(504);
    const body = (await res.json()) as {
      ok: boolean;
      status: string;
      error: string;
      attempts: number;
    };
    expect(body.ok).toBe(false);
    expect(body.status).toBe("error");
    expect(body.error).toBe("Upstream probe request timed out or failed");
    expect(body.attempts).toBe(2);
    expect(callCount).toBe(2);
  });
});
