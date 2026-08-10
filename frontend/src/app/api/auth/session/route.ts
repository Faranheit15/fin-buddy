import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { ACCESS_COOKIE, EXPIRES_COOKIE, REFRESH_COOKIE } from "@/lib/auth/session";

const NO_STORE_HEADERS = {
  "Cache-Control": "no-store, private",
  Pragma: "no-cache",
  Vary: "Cookie",
};

function isSameOriginRequest(request: Request): boolean {
  const origin = request.headers.get("origin");
  if (!origin) return false;
  try {
    return new URL(origin).origin === new URL(request.url).origin;
  } catch {
    return false;
  }
}

function forbiddenResponse() {
  return NextResponse.json(
    { error: "Cross-site session changes are not allowed" },
    { status: 403, headers: NO_STORE_HEADERS },
  );
}

/**
 * Exposes only non-secret session state to browser code. Tokens stay readable
 * exclusively by same-origin Next.js route handlers.
 */
export async function GET() {
  const jar = await cookies();
  const expiresRaw = jar.get(EXPIRES_COOKIE)?.value;
  const expiresAt = expiresRaw ? Number(expiresRaw) : null;
  const authenticated = Boolean(jar.get(ACCESS_COOKIE)?.value);

  return NextResponse.json(
    {
      session: authenticated
        ? { authenticated: true, expiresAt: Number.isFinite(expiresAt) ? expiresAt : null }
        : null,
    },
    { headers: NO_STORE_HEADERS },
  );
}

export async function DELETE(request: Request) {
  if (!isSameOriginRequest(request)) return forbiddenResponse();
  const jar = await cookies();
  jar.delete(ACCESS_COOKIE);
  jar.delete(REFRESH_COOKIE);
  jar.delete(EXPIRES_COOKIE);
  return NextResponse.json({ ok: true }, { headers: NO_STORE_HEADERS });
}
