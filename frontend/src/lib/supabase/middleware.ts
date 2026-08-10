import { type NextRequest, NextResponse } from "next/server";

import { ACCESS_COOKIE } from "@/lib/auth/session";

/**
 * Route protection using credentials stored as HttpOnly cookies on this origin.
 * Auth is performed by FastAPI through the server-side BFF; this only gates UI routes.
 */
export async function updateSession(
  request: NextRequest,
  requestHeaders = new Headers(request.headers),
) {
  const response = NextResponse.next({ request: { headers: requestHeaders } });
  const accessToken = request.cookies.get(ACCESS_COOKIE)?.value;
  const pathname = request.nextUrl.pathname;

  const isAppRoute = pathname === "/app" || pathname.startsWith("/app/");
  const isAuthPage = pathname === "/login" || pathname === "/signup";

  if (isAppRoute && !accessToken) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = "/login";
    redirectUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(redirectUrl);
  }

  if (isAuthPage && accessToken) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = "/app";
    redirectUrl.search = "";
    return NextResponse.redirect(redirectUrl);
  }

  return response;
}
