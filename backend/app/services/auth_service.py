"""Authentication orchestration over Supabase Auth + local bootstrap."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AppError
from app.infrastructure.supabase_auth import SupabaseAuthClient, extract_user_id
from app.models.enums import ActivityAction
from app.models.organization import Organization
from app.models.profile import Profile
from app.services.logging_service import log_activity
from app.services.user_service import ensure_profile_and_org


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
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[Profile | None, Organization | None, dict[str, Any], dict[str, Any]]:
    client = SupabaseAuthClient(settings)
    data = {"full_name": display_name} if display_name else None
    auth_response = await client.sign_up_email(email, password, data=data)

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
    return await client.sign_in_magic_link(email, redirect_to=redirect_to)


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


def google_oauth_url(settings: Settings, *, redirect_to: str) -> str:
    if not settings.supabase_url:
        raise AppError("Supabase URL not configured", code="auth_not_configured", status_code=503)
    from urllib.parse import quote

    base = settings.supabase_url.rstrip("/")
    return (
        f"{base}/auth/v1/authorize?provider=google&redirect_to={quote(redirect_to, safe='')}"
    )
