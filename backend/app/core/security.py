"""JWT verification and auth dependencies."""

from dataclasses import dataclass
from typing import Annotated, Any
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.db.session import get_db
from app.models.enums import OrgRole, PlatformRole
from app.models.organization import OrganizationMember
from app.models.profile import Profile

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class AuthUser:
    """Authenticated principal from Supabase JWT + local profile."""

    id: UUID
    email: str | None
    phone: str | None
    platform_role: PlatformRole
    raw_claims: dict[str, Any]


def decode_supabase_jwt(token: str, settings: Settings) -> dict[str, Any]:
    secret = settings.supabase_jwt_secret
    if not secret:
        if settings.demo_login_allowed:
            secret = "fin-buddy-demo-dev-secret-change-me"
        else:
            raise UnauthorizedError("JWT secret is not configured")

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=settings.supabase_jwt_audience,
            options={"require": ["exp", "sub"]},
        )
    except PyJWTError as exc:
        raise UnauthorizedError(f"Invalid token: {exc}") from exc

    # Demo tokens use our issuer; Supabase tokens use project issuer — accept either.
    if settings.supabase_jwt_issuer:
        iss = str(payload.get("iss") or "").rstrip("/")
        expected = settings.supabase_jwt_issuer.rstrip("/")
        is_demo = (payload.get("app_metadata") or {}).get("provider") == "demo"
        if (
            iss
            and not is_demo
            and iss != expected
            and not expected.startswith(iss)
            and not iss.startswith(expected.removesuffix("/auth/v1"))
        ):
            raise UnauthorizedError("Invalid token issuer")

    return payload


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not settings.auth_configured and not settings.demo_login_allowed:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured (set Supabase env vars)",
        )

    claims = decode_supabase_jwt(credentials.credentials, settings)
    user_id = UUID(str(claims["sub"]))

    result = await db.execute(select(Profile).where(Profile.id == user_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        # Lazy profile bootstrap will often run from /auth/me or login; still allow token
        email = claims.get("email")
        phone = claims.get("phone")
        return AuthUser(
            id=user_id,
            email=email,
            phone=phone,
            platform_role=PlatformRole.USER,
            raw_claims=claims,
        )

    if not profile.is_active:
        raise ForbiddenError("Account is disabled")

    return AuthUser(
        id=profile.id,
        email=profile.email,
        phone=profile.phone,
        platform_role=profile.platform_role,
        raw_claims=claims,
    )


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthUser | None:
    if credentials is None:
        return None
    return await get_current_user(credentials, settings, db)


def require_platform_admin(user: AuthUser) -> AuthUser:
    if user.platform_role not in (PlatformRole.ADMIN, PlatformRole.SUPER_ADMIN):
        raise ForbiddenError("Platform admin access required")
    return user


async def get_platform_admin(
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> AuthUser:
    return require_platform_admin(user)


async def require_org_member(
    org_id: UUID,
    user: AuthUser,
    db: AsyncSession,
    *,
    min_role: OrgRole | None = None,
) -> OrganizationMember:
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise ForbiddenError("Not a member of this organization")

    if min_role is not None:
        rank = {OrgRole.MEMBER: 1, OrgRole.ADMIN: 2, OrgRole.OWNER: 3}
        if rank[member.role] < rank[min_role]:
            raise ForbiddenError("Insufficient organization role")
    return member


async def get_active_org_id(
    x_organization_id: Annotated[UUID | None, Header(alias="X-Organization-Id")] = None,
) -> UUID | None:
    return x_organization_id
