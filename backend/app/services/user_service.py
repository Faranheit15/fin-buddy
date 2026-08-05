"""Profile + personal organization bootstrap."""

import re
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.enums import ActivityAction, OrgRole, PlatformRole
from app.models.organization import Organization, OrganizationMember
from app.models.profile import Profile
from app.services.category_service import seed_default_categories
from app.services.logging_service import log_activity

_LAST_LOGIN_TOUCH_AFTER = timedelta(hours=1)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (slug or "workspace")[:60]


async def get_profile(session: AsyncSession, user_id: UUID) -> Profile | None:
    result = await session.execute(select(Profile).where(Profile.id == user_id))
    return result.scalar_one_or_none()


async def ensure_profile_and_org(
    session: AsyncSession,
    *,
    user_id: UUID,
    email: str | None,
    phone: str | None,
    display_name: str | None,
    avatar_url: str | None,
    settings: Settings,
    user_metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[Profile, Organization]:
    """
    Create profile + personal org on first login if missing.
    Elevates platform_role when email is in PLATFORM_ADMIN_EMAILS.
    """
    profile = await get_profile(session, user_id)
    created_profile = False

    admin_emails = {e.lower() for e in settings.platform_admin_emails}
    is_platform_admin = bool(email and email.lower() in admin_emails)

    if profile is None:
        role = PlatformRole.SUPER_ADMIN if is_platform_admin else PlatformRole.USER
        name = (
            display_name
            or (user_metadata or {}).get("full_name")
            or (email.split("@")[0] if email else "User")
        )
        profile = Profile(
            id=user_id,
            email=email,
            phone=phone,
            display_name=name,
            avatar_url=avatar_url or (user_metadata or {}).get("avatar_url"),
            platform_role=role,
            last_login_at=datetime.now(UTC),
        )
        session.add(profile)
        await session.flush()
        created_profile = True
    else:
        if email and email != profile.email:
            profile.email = email
        if phone and phone != profile.phone:
            profile.phone = phone
        if display_name and display_name != profile.display_name:
            profile.display_name = display_name
        if avatar_url and avatar_url != profile.avatar_url:
            profile.avatar_url = avatar_url
        now = datetime.now(UTC)
        last_login = profile.last_login_at
        if last_login is not None and last_login.tzinfo is None:
            last_login = last_login.replace(tzinfo=UTC)
        if last_login is None or last_login < now - _LAST_LOGIN_TOUCH_AFTER:
            profile.last_login_at = now
        if is_platform_admin and profile.platform_role == PlatformRole.USER:
            profile.platform_role = PlatformRole.SUPER_ADMIN

    # Ensure at least one org membership
    result = await session.execute(
        select(OrganizationMember).where(OrganizationMember.user_id == user_id).limit(1)
    )
    membership = result.scalar_one_or_none()

    if membership is None:
        base = _slugify(profile.display_name or profile.email or "workspace")
        slug = f"{base}-{str(uuid4())[:8]}"
        org = Organization(
            id=uuid4(),
            name=f"{profile.display_name or 'My'} Workspace",
            slug=slug,
        )
        session.add(org)
        await session.flush()
        membership = OrganizationMember(
            id=uuid4(),
            organization_id=org.id,
            user_id=user_id,
            role=OrgRole.OWNER,
        )
        session.add(membership)
        await session.flush()

        await seed_default_categories(session, org.id)
        await session.flush()

        await log_activity(
            session,
            action=ActivityAction.ORG_CREATE,
            summary=f"Created personal workspace {org.name}",
            actor_user_id=user_id,
            organization_id=org.id,
            resource_type="organization",
            resource_id=str(org.id),
            ip_address=ip_address,
            user_agent=user_agent,
        )
    else:
        org_result = await session.execute(
            select(Organization).where(Organization.id == membership.organization_id)
        )
        org = org_result.scalar_one()

    if created_profile:
        await log_activity(
            session,
            action=ActivityAction.SIGNUP,
            summary="Profile created",
            actor_user_id=user_id,
            organization_id=org.id,
            resource_type="profile",
            resource_id=str(user_id),
            ip_address=ip_address,
            user_agent=user_agent,
        )

    if session.new or session.dirty or session.deleted:
        await session.commit()
        await session.refresh(profile)
        await session.refresh(org)
    return profile, org
