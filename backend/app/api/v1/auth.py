"""Authentication endpoints (Supabase Auth + local profile bootstrap)."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AppSettings, CurrentUser, DbSession, client_meta
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.rate_limit import AUTH_LIMIT, enforce_rate_limit
from app.models.enums import ActivityAction, OrgRole
from app.models.organization import Organization, OrganizationMember
from app.models.profile import Profile
from app.schemas.auth import (
    AuthResponse,
    GoogleOAuthResponse,
    LoginRequest,
    MagicLinkRequest,
    MeResponse,
    OrganizationSummary,
    OrganizationUpdate,
    PhoneOtpRequest,
    ProfileResponse,
    ProfileUpdate,
    RefreshRequest,
    SessionFromTokensRequest,
    SignUpRequest,
    TokenPair,
    VerifyOtpRequest,
)
from app.schemas.common import MessageResponse
from app.services import auth_service
from app.services.demo_auth import demo_login
from app.services.logging_service import log_activity

router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_rate_limit(request: Request) -> None:
    enforce_rate_limit(request, bucket="auth", limit=AUTH_LIMIT, window_seconds=60.0)


def _profile_out(profile: Any) -> ProfileResponse:
    return ProfileResponse.model_validate(profile)


def _org_out(org: Organization, role: OrgRole) -> OrganizationSummary:
    return OrganizationSummary(id=org.id, name=org.name, slug=org.slug, role=role)


async def _membership_role(db: AsyncSession, user_id: UUID, org_id: UUID) -> OrgRole:
    result = await db.execute(
        select(OrganizationMember.role).where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.organization_id == org_id,
        )
    )
    role = result.scalar_one_or_none()
    return role or OrgRole.OWNER


@router.post("/signup", response_model=AuthResponse)
async def signup(
    body: SignUpRequest,
    request: Request,
    db: DbSession,
    settings: AppSettings,
) -> AuthResponse:
    _auth_rate_limit(request)
    ip, ua = client_meta(request)
    profile, org, tokens, raw = await auth_service.signup_with_email(
        db,
        settings,
        email=body.email,
        password=body.password,
        display_name=body.display_name,
        email_redirect_to=body.redirect_to,
        ip_address=ip,
        user_agent=ua,
    )
    if profile is None or org is None:
        return AuthResponse(
            message="Signup initiated. Check your email to confirm if confirmation is enabled.",
            raw=raw,
            session=TokenPair(**tokens) if tokens else None,
        )
    role = await _membership_role(db, profile.id, org.id)
    return AuthResponse(
        user=_profile_out(profile),
        organization=_org_out(org, role),
        session=TokenPair(**tokens),
        message="Signed up successfully",
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: DbSession,
    settings: AppSettings,
) -> AuthResponse:
    _auth_rate_limit(request)
    ip, ua = client_meta(request)
    profile, org, tokens = await auth_service.login_with_email(
        db,
        settings,
        email=body.email,
        password=body.password,
        ip_address=ip,
        user_agent=ua,
    )
    role = await _membership_role(db, profile.id, org.id)
    return AuthResponse(
        user=_profile_out(profile),
        organization=_org_out(org, role),
        session=TokenPair(**tokens),
        message="Logged in",
    )


@router.post("/demo-login", response_model=AuthResponse)
async def demo_login_endpoint(
    request: Request,
    db: DbSession,
    settings: AppSettings,
) -> AuthResponse:
    """
    Development demo login — skips Supabase email entirely.
    Enabled in development/test by default; disabled in production.
    """
    if not settings.demo_login_allowed:
        raise ForbiddenError("Demo login is disabled", code="demo_auth_disabled")
    _auth_rate_limit(request)
    ip, ua = client_meta(request)
    profile, org, tokens = await demo_login(
        db, settings, ip_address=ip, user_agent=ua
    )
    role = await _membership_role(db, profile.id, org.id)
    return AuthResponse(
        user=_profile_out(profile),
        organization=_org_out(org, role),
        session=TokenPair(**tokens),
        message="Logged in as demo user",
    )


@router.get("/demo-available", response_model=MessageResponse)
async def demo_available(settings: AppSettings) -> MessageResponse:
    if settings.demo_login_allowed:
        return MessageResponse(message="demo_available")
    return MessageResponse(message="demo_disabled")


@router.post("/magic-link", response_model=MessageResponse)
async def magic_link(
    body: MagicLinkRequest,
    request: Request,
    settings: AppSettings,
) -> MessageResponse:
    _auth_rate_limit(request)
    await auth_service.request_magic_link(
        settings, email=body.email, redirect_to=body.redirect_to
    )
    return MessageResponse(message="Magic link sent if the email is valid")


@router.post("/otp/phone", response_model=MessageResponse)
async def phone_otp(
    body: PhoneOtpRequest,
    request: Request,
    settings: AppSettings,
) -> MessageResponse:
    _auth_rate_limit(request)
    await auth_service.send_phone_otp(settings, phone=body.phone)
    return MessageResponse(message="OTP sent if the phone number is valid")


@router.post("/otp/verify", response_model=AuthResponse)
async def verify_otp(
    body: VerifyOtpRequest,
    request: Request,
    db: DbSession,
    settings: AppSettings,
) -> AuthResponse:
    _auth_rate_limit(request)
    ip, ua = client_meta(request)
    profile, org, tokens = await auth_service.verify_otp(
        db,
        settings,
        email=str(body.email) if body.email else None,
        phone=body.phone,
        token=body.token,
        otp_type=body.type,
        ip_address=ip,
        user_agent=ua,
    )
    role = await _membership_role(db, profile.id, org.id)
    return AuthResponse(
        user=_profile_out(profile),
        organization=_org_out(org, role),
        session=TokenPair(**tokens),
        message="Verified",
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    body: RefreshRequest,
    request: Request,
    db: DbSession,
    settings: AppSettings,
) -> AuthResponse:
    _auth_rate_limit(request)
    ip, ua = client_meta(request)
    profile, org, tokens = await auth_service.refresh_session(
        db,
        settings,
        refresh_token=body.refresh_token,
        ip_address=ip,
        user_agent=ua,
    )
    role = await _membership_role(db, profile.id, org.id)
    return AuthResponse(
        user=_profile_out(profile),
        organization=_org_out(org, role),
        session=TokenPair(**tokens),
    )


@router.post("/session", response_model=AuthResponse)
async def establish_session(
    body: SessionFromTokensRequest,
    request: Request,
    db: DbSession,
    settings: AppSettings,
) -> AuthResponse:
    """
    Establish app profile/org from tokens already issued by Supabase
    (OAuth / magic-link redirect completion). Auth verification is server-side.
    """
    _auth_rate_limit(request)
    ip, ua = client_meta(request)
    profile, org, tokens = await auth_service.session_from_tokens(
        db,
        settings,
        access_token=body.access_token,
        refresh_token=body.refresh_token,
        expires_in=body.expires_in,
        expires_at=body.expires_at,
        ip_address=ip,
        user_agent=ua,
    )
    role = await _membership_role(db, profile.id, org.id)
    return AuthResponse(
        user=_profile_out(profile),
        organization=_org_out(org, role),
        session=TokenPair(**tokens),
        message="Session established",
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    settings: AppSettings,
    user: CurrentUser,  # ensures token present
) -> MessageResponse:
    auth = request.headers.get("authorization") or ""
    token = auth.removeprefix("Bearer ").strip()
    if token:
        await auth_service.logout(settings, token)
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=MeResponse)
async def me(
    request: Request,
    db: DbSession,
    settings: AppSettings,
    user: CurrentUser,
) -> MeResponse:
    ip, ua = client_meta(request)
    profile, _org = await auth_service.me_bootstrap(
        db,
        settings,
        user_id=user.id,
        email=user.email,
        phone=user.phone,
        claims=user.raw_claims,
        ip_address=ip,
        user_agent=ua,
    )
    result = await db.execute(
        select(OrganizationMember, Organization)
        .join(Organization, Organization.id == OrganizationMember.organization_id)
        .where(OrganizationMember.user_id == user.id)
    )
    orgs = [
        OrganizationSummary(id=org.id, name=org.name, slug=org.slug, role=member.role)
        for member, org in result.all()
    ]
    return MeResponse(user=_profile_out(profile), organizations=orgs)


@router.patch("/me", response_model=ProfileResponse)
async def update_me(
    body: ProfileUpdate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> ProfileResponse:
    result = await db.execute(select(Profile).where(Profile.id == user.id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise NotFoundError("Profile not found")

    data = body.model_dump(exclude_unset=True)
    if "display_name" in data:
        name = data["display_name"]
        profile.display_name = name.strip() if isinstance(name, str) and name.strip() else name
    if "timezone" in data and data["timezone"]:
        profile.timezone = data["timezone"].strip()
    if "due_soon_days" in data and data["due_soon_days"] is not None:
        profile.due_soon_days = data["due_soon_days"]
    if "high_utilization_percent" in data and data["high_utilization_percent"] is not None:
        profile.high_utilization_percent = data["high_utilization_percent"]

    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.OTHER,
        summary="Updated profile / notification preferences",
        actor_user_id=user.id,
        resource_type="profile",
        resource_id=str(user.id),
        ip_address=ip,
        user_agent=ua,
        metadata=data,
    )
    await db.commit()
    await db.refresh(profile)
    return _profile_out(profile)


@router.patch("/organizations/{org_id}", response_model=OrganizationSummary)
async def update_organization(
    org_id: UUID,
    body: OrganizationUpdate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> OrganizationSummary:
    result = await db.execute(
        select(OrganizationMember, Organization)
        .join(Organization, Organization.id == OrganizationMember.organization_id)
        .where(
            OrganizationMember.user_id == user.id,
            Organization.id == org_id,
        )
    )
    row = result.one_or_none()
    if row is None:
        raise NotFoundError("Organization not found")
    member, org = row
    if member.role not in (OrgRole.OWNER, OrgRole.ADMIN):
        raise ForbiddenError("Only owners and admins can rename the workspace")

    org.name = body.name.strip()
    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.OTHER,
        summary=f"Renamed workspace to {org.name}",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="organization",
        resource_id=str(org.id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.commit()
    await db.refresh(org)
    return _org_out(org, member.role)


@router.get("/oauth/google", response_model=GoogleOAuthResponse)
async def google_oauth(
    request: Request,
    settings: AppSettings,
    redirect_to: str = Query(..., description="Frontend callback URL"),
) -> GoogleOAuthResponse:
    _auth_rate_limit(request)
    url = auth_service.google_oauth_url(settings, redirect_to=redirect_to)
    # Append apikey is handled by Supabase hosted authorize page
    if settings.supabase_anon_key:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}apikey={settings.supabase_anon_key}"
    return GoogleOAuthResponse(url=url)
