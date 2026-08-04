import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import {
  ACCESS_COOKIE,
  EXPIRES_COOKIE,
  REFRESH_COOKIE,
  type StoredSession,
} from "@/lib/auth/session";

const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "";
const useSecureCookies =
  process.env.NODE_ENV === "production" || appUrl.startsWith("https://");

const COOKIE_BASE = {
  httpOnly: true,
  sameSite: "lax" as const,
  secure: useSecureCookies,
  path: "/",
};

/**
 * Persist backend-issued tokens as httpOnly cookies on the Next.js origin
 * so middleware can protect /app without calling Supabase from the browser.
 */
export async function POST(request: Request) {
  const body = (await request.json()) as Partial<StoredSession>;
  if (!body.accessToken) {
    return NextResponse.json({ error: "accessToken required" }, { status: 400 });
  }

  const jar = await cookies();
  const maxAge = body.expiresAt
    ? Math.max(body.expiresAt - Math.floor(Date.now() / 1000), 60)
    : 60 * 60 * 24 * 7;

  jar.set(ACCESS_COOKIE, body.accessToken, { ...COOKIE_BASE, maxAge });
  if (body.refreshToken) {
    jar.set(REFRESH_COOKIE, body.refreshToken, { ...COOKIE_BASE, maxAge: 60 * 60 * 24 * 30 });
  } else {
    jar.delete(REFRESH_COOKIE);
  }
  if (body.expiresAt) {
    jar.set(EXPIRES_COOKIE, String(body.expiresAt), { ...COOKIE_BASE, maxAge });
  }

  return NextResponse.json({ ok: true });
}

export async function GET() {
  const jar = await cookies();
  const accessToken = jar.get(ACCESS_COOKIE)?.value ?? null;
  const refreshToken = jar.get(REFRESH_COOKIE)?.value ?? null;
  const expiresRaw = jar.get(EXPIRES_COOKIE)?.value;
  const expiresAt = expiresRaw ? Number(expiresRaw) : null;

  if (!accessToken) {
    return NextResponse.json({ session: null });
  }

  return NextResponse.json({
    session: {
      accessToken,
      refreshToken,
      expiresAt: Number.isFinite(expiresAt) ? expiresAt : null,
    } satisfies StoredSession,
  });
}

export async function DELETE() {
  const jar = await cookies();
  jar.delete(ACCESS_COOKIE);
  jar.delete(REFRESH_COOKIE);
  jar.delete(EXPIRES_COOKIE);
  return NextResponse.json({ ok: true });
}
