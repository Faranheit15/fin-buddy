import { type NextRequest, NextResponse } from "next/server";

import { ACCESS_COOKIE } from "@/lib/auth/session";

/**
 * Route protection using backend-issued tokens stored as cookies on this origin.
 * Auth is performed by FastAPI; this only gates UI routes.
 */
export async function updateSession(request: NextRequest) {
  const response = NextResponse.next({ request });
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
