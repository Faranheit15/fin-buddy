import { afterEach, beforeEach, describe, expect, mock, test } from "bun:test";
import { GET } from "./route";

const originalFetch = globalThis.fetch;

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

  test("proxies upstream /ready with cache: no-store and returns 200 on success", async () => {
    let capturedUrl = "";
    let capturedInit: RequestInit | undefined;

    globalThis.fetch = mock(async (input: RequestInfo | URL, init?: RequestInit) => {
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
    const body = (await res.json()) as { ok: boolean; status: string; requestId: string };
    expect(body.ok).toBe(true);
    expect(body.status).toBe("ok");
    expect(body.requestId).toMatch(/^cron-keepalive-/);

    expect(capturedUrl).toBe("http://127.0.0.1:8001/api/v1/ready");
    expect(capturedInit?.cache).toBe("no-store");
    const headers = capturedInit?.headers as Record<string, string>;
    expect(headers?.["User-Agent"]).toBe("fin-buddy-cron/1.0");
    expect(headers?.["X-Request-Id"]).toBe(body.requestId);
    expect(headers?.["Cookie"]).toBeUndefined();
  });

  test("returns 503 degraded when upstream returns non-200", async () => {
    globalThis.fetch = mock(async () => {
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
    const body = (await res.json()) as { ok: boolean; status: string; upstreamStatus: number };
    expect(body.ok).toBe(false);
    expect(body.status).toBe("degraded");
    expect(body.upstreamStatus).toBe(503);
  });

  test("returns 504 error when upstream request fails or times out", async () => {
    globalThis.fetch = mock(async () => {
      throw new Error("Connection timed out");
    }) as unknown as typeof fetch;

    const req = new Request("http://localhost:3000/api/cron/supabase-keepalive", {
      headers: { authorization: "Bearer mock-secret-1234" },
    });

    const res = await GET(req);
    expect(res.status).toBe(504);
    const body = (await res.json()) as { ok: boolean; status: string; error: string };
    expect(body.ok).toBe(false);
    expect(body.status).toBe("error");
    expect(body.error).toBe("Upstream probe request timed out or failed");
  });
});
