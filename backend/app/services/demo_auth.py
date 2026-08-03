"""Development demo login — no Supabase email, mint JWT with project secret."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AppError, ForbiddenError
from app.models.enums import ActivityAction, PlatformRole
from app.models.organization import Organization
from app.models.profile import Profile
from app.services.logging_service import log_activity
from app.services.user_service import ensure_profile_and_org

# Stable demo user id (not a real Supabase auth user)
DEMO_USER_ID = UUID("00000000-0000-4000-8000-0000000000d1")
TOKEN_TTL_HOURS = 24 * 7


def _mint_demo_jwt(settings: Settings, *, email: str, user_id: UUID) -> dict[str, Any]:
    secret = settings.supabase_jwt_secret
    if not secret:
        # Local fallback when JWT secret is missing — still only if demo is allowed
        secret = "fin-buddy-demo-dev-secret-change-me"

    now = datetime.now(UTC)
    exp = now + timedelta(hours=TOKEN_TTL_HOURS)
    issuer = settings.supabase_jwt_issuer or "http://localhost/auth/v1"
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": "authenticated",
        "aud": settings.supabase_jwt_audience or "authenticated",
        "iss": issuer,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "app_metadata": {"provider": "demo", "providers": ["demo"]},
        "user_metadata": {
            "full_name": settings.demo_user_name,
            "demo": True,
        },
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return {
        "access_token": token,
        "refresh_token": f"demo-refresh-{user_id}",
        "expires_in": TOKEN_TTL_HOURS * 3600,
        "expires_at": int(exp.timestamp()),
        "token_type": "bearer",
    }


async def demo_login(
    session: AsyncSession,
    settings: Settings,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[Profile, Organization, dict[str, Any]]:
    if not settings.demo_login_allowed:
        raise ForbiddenError(
            "Demo login is disabled (production or DEMO_AUTH_ENABLED=false)",
            code="demo_auth_disabled",
        )
    if not settings.database_configured:
        raise AppError(
            "Database is not configured",
            code="database_not_configured",
            status_code=503,
        )

    email = settings.demo_user_email
    profile, org = await ensure_profile_and_org(
        session,
        user_id=DEMO_USER_ID,
        email=email,
        phone=None,
        display_name=settings.demo_user_name,
        avatar_url=None,
        settings=settings,
        user_metadata={"full_name": settings.demo_user_name, "demo": True},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Elevate demo user for admin panel exploration in dev
    if profile.platform_role == PlatformRole.USER:
        result = await session.execute(select(Profile).where(Profile.id == DEMO_USER_ID))
        row = result.scalar_one()
        row.platform_role = PlatformRole.SUPER_ADMIN
        await session.commit()
        await session.refresh(row)
        profile = row

    tokens = _mint_demo_jwt(settings, email=email, user_id=DEMO_USER_ID)
    await log_activity(
        session,
        action=ActivityAction.LOGIN,
        summary="Demo login",
        actor_user_id=DEMO_USER_ID,
        organization_id=org.id,
        resource_type="profile",
        resource_id=str(DEMO_USER_ID),
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={"demo": True},
        commit=True,
    )
    return profile, org, tokens
