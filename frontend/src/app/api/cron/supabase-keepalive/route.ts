import crypto from "node:crypto";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const NO_STORE_HEADERS = {
  "Cache-Control": "no-store, no-cache, must-revalidate",
  Pragma: "no-cache",
};

export async function GET(request: Request): Promise<NextResponse> {
  if (process.env.ENABLE_KEEPALIVE_CRON === "false") {
    return NextResponse.json(
      { ok: false, message: "Keepalive cron is disabled" },
      { status: 200, headers: NO_STORE_HEADERS }
    );
  }

  const configuredSecret = process.env.CRON_SECRET;
  if (!configuredSecret) {
    return NextResponse.json(
      { ok: false, error: "CRON_SECRET is not configured" },
      { status: 503, headers: NO_STORE_HEADERS }
    );
  }

  const authHeader = request.headers.get("authorization");
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return NextResponse.json(
      { ok: false, error: "Unauthorized" },
      { status: 401, headers: NO_STORE_HEADERS }
    );
  }

  const providedToken = authHeader.slice(7).trim();
  const providedBuffer = Buffer.from(providedToken);
  const secretBuffer = Buffer.from(configuredSecret);

  if (
    providedBuffer.length !== secretBuffer.length ||
    !crypto.timingSafeEqual(providedBuffer, secretBuffer)
  ) {
    return NextResponse.json(
      { ok: false, error: "Unauthorized" },
      { status: 401, headers: NO_STORE_HEADERS }
    );
  }

  const backendUrl = (process.env.BACKEND_URL || "http://127.0.0.1:8001").replace(/\/$/, "");
  const requestId = `cron-keepalive-${crypto.randomUUID()}`;

  try {
    const upstreamRes = await fetch(`${backendUrl}/api/v1/ready`, {
      method: "GET",
      headers: {
        Accept: "application/json",
        "User-Agent": "fin-buddy-cron/1.0",
        "X-Request-Id": requestId,
      },
      cache: "no-store",
      signal: AbortSignal.timeout(8000),
    });

    if (upstreamRes.ok) {
      const data = (await upstreamRes.json().catch(() => ({}))) as { status?: string };
      return NextResponse.json(
        {
          ok: true,
          status: data.status || "ok",
          requestId,
          timestamp: new Date().toISOString(),
        },
        { status: 200, headers: { ...NO_STORE_HEADERS, "X-Request-Id": requestId } }
      );
    }

    return NextResponse.json(
      {
        ok: false,
        status: "degraded",
        requestId,
        upstreamStatus: upstreamRes.status,
      },
      { status: 503, headers: { ...NO_STORE_HEADERS, "X-Request-Id": requestId } }
    );
  } catch {
    return NextResponse.json(
      {
        ok: false,
        status: "error",
        requestId,
        error: "Upstream probe request timed out or failed",
      },
      { status: 504, headers: { ...NO_STORE_HEADERS, "X-Request-Id": requestId } }
    );
  }
}
