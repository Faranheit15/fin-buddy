"""Authentication orchestration over Supabase Auth + local bootstrap."""

import re
from typing import Any
from urllib.parse import unquote, urlencode, urlsplit, urlunsplit
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AppError
from app.infrastructure.supabase_auth import SupabaseAuthClient, extract_user_id
from app.models.enums import ActivityAction, OrgRole
from app.models.organization import Organization, OrganizationMember
from app.models.profile import Profile
from app.services.logging_service import log_activity
from app.services.user_service import ensure_profile_and_org

_SAFE_STATE_RE = re.compile(r"^[A-Za-z0-9_-]{8,256}$")
_SAFE_CHALLENGE_RE = re.compile(r"^[A-Za-z0-9_-]{43,128}$")


def validate_safe_destination(destination: str | None) -> str:
    """
    Validate that destination is a safe, same-origin relative app path.
    Rejects external URLs, protocol-relative URLs (//), backslashes, fragments (#),
    path traversal (/../), control characters, and non-app paths.
    Always falls back safely to '/app'.
    """
    if not destination or not isinstance(destination, str):
        return "/app"
    clean = destination.strip()
    if not clean:
        return "/app"
    # Reject protocol-relative, backslashes, or fragments
    if clean.startswith("//") or "\\" in clean or "#" in clean:
        return "/app"
    # Reject CRLF or control characters
    if any(ord(c) < 32 or ord(c) == 127 for c in clean):
        return "/app"
    # Must start with single /
    if not clean.startswith("/"):
        return "/app"
    try:
        parsed = urlsplit(clean)
    except ValueError:
        return "/app"
    # Reject if scheme or netloc is present
    if parsed.scheme or parsed.netloc:
        return "/app"
    # Check for traversal in path segments
    path = parsed.path
    unquoted = unquote(path)
    if any(s in ("..", ".") for s in [seg for seg in unquoted.split("/") if seg]):
        return "/app"
    segments = [s for s in path.split("/") if s]
    if any(s in ("..", ".") for s in segments):
        return "/app"
    # Must be /app or /app/...
    if path != "/app" and not path.startswith("/app/"):
        return "/app"
    # Reconstruct clean path + search
    reconstructed = path
    if parsed.query:
        reconstructed += f"?{parsed.query}"
    return reconstructed


def _validate_code_challenge(code_challenge: str, method: str | None) -> None:
    if not _SAFE_CHALLENGE_RE.match(code_challenge):
        raise AppError(
            "Invalid code_challenge: must be base64url string between 43 and 128 characters",
            code="invalid_code_challenge",
            status_code=400,
        )
    if method and method.lower() not in {"s256", "sha256"}:
        raise AppError(
            "code_challenge_method must be s256",
            code="invalid_code_challenge_method",
            status_code=400,
        )


def _validate_oauth_state(state: str) -> None:
    if not _SAFE_STATE_RE.match(state):
        raise AppError(
            "Invalid OAuth state: must be urlsafe string between 8 and 256 characters",
            code="invalid_oauth_state",
            status_code=400,
        )


def _frontend_callback_url(settings: Settings, requested: str | None) -> str:
    """Return the single trusted frontend callback URL for all auth redirects."""
    if not settings.frontend_app_url:
        raise AppError(
            "FRONTEND_APP_URL must be configured for browser authentication",
            code="frontend_url_not_configured",
            status_code=503,
        )
    try:
        frontend = urlsplit(settings.frontend_app_url)
    except ValueError as exc:
        raise AppError(
            "FRONTEND_APP_URL is invalid", code="frontend_url_invalid", status_code=500
        ) from exc
    if frontend.scheme not in {"http", "https"} or not frontend.netloc:
        raise AppError("FRONTEND_APP_URL is invalid", code="frontend_url_invalid", status_code=500)

    callback = urlunsplit((frontend.scheme, frontend.netloc, "/auth/callback", "", ""))
    if requested is None:
        return callback

    try:
        candidate = urlsplit(requested)
    except ValueError as exc:
        raise AppError("Invalid authentication redirect URL", code="invalid_redirect") from exc
    if (
        candidate.query
        or candidate.fragment
        or candidate.scheme != frontend.scheme
        or candidate.netloc != frontend.netloc
        or candidate.path != "/auth/callback"
        or urlunsplit((candidate.scheme, candidate.netloc, candidate.path, "", "")) != callback
    ):
        raise AppError("Invalid authentication redirect URL", code="invalid_redirect")
    return callback


def _session_payload(auth_response: dict[str, Any]) -> dict[str, Any]:
    return {
        "access_token": auth_response.get("access_token"),
        "refresh_token": auth_response.get("refresh_token"),
        "expires_in": auth_response.get("expires_in"),
        "expires_at": auth_response.get("expires_at"),
        "token_type": auth_response.get("token_type", "bearer"),
    }


async def _bootstrap_from_auth_response(
    session: AsyncSession,
    auth_response: dict[str, Any],
    settings: Settings,
    *,
    ip_address: str | None,
    user_agent: str | None,
    action: ActivityAction,
) -> tuple[Profile, Organization, dict[str, Any]]:
    user = auth_response.get("user") or {}
    if not user and auth_response.get("access_token"):
        client = SupabaseAuthClient(settings)
        user = await client.get_user(auth_response["access_token"])
        auth_response = {**auth_response, "user": user}

    user_id = extract_user_id(auth_response)
    meta = user.get("user_metadata") or {}
    profile, org = await ensure_profile_and_org(
        session,
        user_id=user_id,
        email=user.get("email"),
        phone=user.get("phone"),
        display_name=meta.get("full_name") or meta.get("name"),
        avatar_url=meta.get("avatar_url"),
        settings=settings,
        user_metadata=meta,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await log_activity(
        session,
        action=action,
        summary=f"User {action.value}",
        actor_user_id=profile.id,
        organization_id=org.id,
        resource_type="profile",
        resource_id=str(profile.id),
        ip_address=ip_address,
        user_agent=user_agent,
        commit=True,
    )
    return profile, org, _session_payload(auth_response)


async def signup_with_email(
    session: AsyncSession,
    settings: Settings,
    *,
    email: str,
    password: str,
    display_name: str | None,
    email_redirect_to: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[Profile | None, Organization | None, dict[str, Any], dict[str, Any]]:
    client = SupabaseAuthClient(settings)
    data = {"full_name": display_name} if display_name else None
    redirect = _frontend_callback_url(settings, email_redirect_to)
    auth_response = await client.sign_up_email(
        email,
        password,
        data=data,
        email_redirect_to=redirect,
    )

    # Email confirmation may leave session empty
    if not auth_response.get("access_token"):
        return None, None, {}, auth_response

    profile, org, tokens = await _bootstrap_from_auth_response(
        session,
        auth_response,
        settings,
        ip_address=ip_address,
        user_agent=user_agent,
        action=ActivityAction.SIGNUP,
    )
    return profile, org, tokens, auth_response


async def login_with_email(
    session: AsyncSession,
    settings: Settings,
    *,
    email: str,
    password: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[Profile, Organization, dict[str, Any]]:
    client = SupabaseAuthClient(settings)
    auth_response = await client.sign_in_email(email, password)
    profile, org, tokens = await _bootstrap_from_auth_response(
        session,
        auth_response,
        settings,
        ip_address=ip_address,
        user_agent=user_agent,
        action=ActivityAction.LOGIN,
    )
    return profile, org, tokens


async def request_magic_link(
    settings: Settings,
    *,
    email: str,
    redirect_to: str | None,
) -> dict[str, Any]:
    client = SupabaseAuthClient(settings)
    redirect = _frontend_callback_url(settings, redirect_to)
    return await client.sign_in_magic_link(email, redirect_to=redirect)


async def send_phone_otp(settings: Settings, *, phone: str) -> dict[str, Any]:
    client = SupabaseAuthClient(settings)
    return await client.send_phone_otp(phone)


async def verify_otp(
    session: AsyncSession,
    settings: Settings,
    *,
    email: str | None,
    phone: str | None,
    token: str,
    otp_type: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[Profile, Organization, dict[str, Any]]:
    client = SupabaseAuthClient(settings)
    auth_response = await client.verify_otp(email=email, phone=phone, token=token, type=otp_type)
    profile, org, tokens = await _bootstrap_from_auth_response(
        session,
        auth_response,
        settings,
        ip_address=ip_address,
        user_agent=user_agent,
        action=ActivityAction.LOGIN,
    )
    return profile, org, tokens


async def refresh_session(
    session: AsyncSession,
    settings: Settings,
    *,
    refresh_token: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[Profile, Organization, dict[str, Any]]:
    client = SupabaseAuthClient(settings)
    auth_response = await client.refresh_token(refresh_token)
    profile, org, tokens = await _bootstrap_from_auth_response(
        session,
        auth_response,
        settings,
        ip_address=ip_address,
        user_agent=user_agent,
        action=ActivityAction.TOKEN_REFRESH,
    )
    return profile, org, tokens


async def logout(settings: Settings, access_token: str) -> None:
    client = SupabaseAuthClient(settings)
    await client.logout(access_token)


async def me_bootstrap(
    session: AsyncSession,
    settings: Settings,
    *,
    user_id: UUID,
    email: str | None,
    phone: str | None,
    claims: dict[str, Any],
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[Profile, Organization]:
    meta = claims.get("user_metadata") or {}
    return await ensure_profile_and_org(
        session,
        user_id=user_id,
        email=email,
        phone=phone,
        display_name=meta.get("full_name") or meta.get("name"),
        avatar_url=meta.get("avatar_url"),
        settings=settings,
        user_metadata=meta,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def session_from_code(
    session: AsyncSession,
    settings: Settings,
    *,
    code: str,
    code_verifier: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[Profile, Organization, dict[str, Any]]:
    """
    Exchange a PKCE authorization code with Supabase Auth for session tokens,
    bootstrap local profile/org, and return a session payload.
    """
    client = SupabaseAuthClient(settings)
    auth_response = await client.exchange_pkce_code(code, code_verifier)
    profile, org, tokens = await _bootstrap_from_auth_response(
        session,
        auth_response,
        settings,
        ip_address=ip_address,
        user_agent=user_agent,
        action=ActivityAction.LOGIN,
    )
    return profile, org, tokens


async def session_from_tokens(
    session: AsyncSession,
    settings: Settings,
    *,
    access_token: str,
    refresh_token: str | None = None,
    expires_in: int | None = None,
    expires_at: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[Profile, Organization, dict[str, Any]]:
    """
    Validate an already-issued Supabase access token (e.g. after OAuth redirect),
    bootstrap local profile/org, and return a session payload.
    """
    auth_response: dict[str, Any] = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "expires_at": expires_at,
        "token_type": "bearer",
    }
    return await _bootstrap_from_auth_response(
        session,
        auth_response,
        settings,
        ip_address=ip_address,
        user_agent=user_agent,
        action=ActivityAction.LOGIN,
    )


def google_oauth_url(
    settings: Settings,
    *,
    redirect_to: str | None = None,
    code_challenge: str | None = None,
    code_challenge_method: str | None = None,
    state: str | None = None,
) -> str:
    if not settings.supabase_url:
        raise AppError("Supabase URL not configured", code="auth_not_configured", status_code=503)

    base = settings.supabase_url.rstrip("/")
    callback = _frontend_callback_url(settings, redirect_to)
    params: list[tuple[str, str]] = [
        ("provider", "google"),
        ("redirect_to", callback),
    ]
    if code_challenge:
        _validate_code_challenge(code_challenge, code_challenge_method)
        params.append(("code_challenge", code_challenge))
        params.append(("code_challenge_method", (code_challenge_method or "s256").lower()))
    if state:
        _validate_oauth_state(state)
        params.append(("state", state))

    query = urlencode(params)
    return f"{base}/auth/v1/authorize?{query}"


async def delete_account(
    session: AsyncSession,
    settings: Settings,
    user_id: UUID,
) -> None:
    from sqlalchemy import select

    # 1. Delete all organizations where user is owner
    result = await session.execute(
        select(Organization)
        .join(OrganizationMember)
        .where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.role == OrgRole.OWNER,
        )
    )
    for org in result.scalars().all():
        await session.delete(org)

    # 2. Delete the profile itself
    prof_result = await session.execute(select(Profile).where(Profile.id == user_id))
    profile = prof_result.scalar_one_or_none()
    if profile:
        await session.delete(profile)

    await session.commit()

    # 3. Delete from Supabase Auth
    client = SupabaseAuthClient(settings)
    await client.admin_delete_user(user_id)
