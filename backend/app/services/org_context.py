"""Resolve active organization for a request."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.security import AuthUser
from app.models.organization import Organization, OrganizationMember


async def resolve_organization(
    session: AsyncSession,
    user: AuthUser,
    organization_id: UUID | None,
) -> tuple[Organization, OrganizationMember]:
    if organization_id is None:
        result = await session.execute(
            select(OrganizationMember)
            .where(OrganizationMember.user_id == user.id)
            .order_by(OrganizationMember.created_at.asc())
            .limit(1)
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise ForbiddenError("User has no organization membership")
    else:
        result = await session.execute(
            select(OrganizationMember).where(
                OrganizationMember.user_id == user.id,
                OrganizationMember.organization_id == organization_id,
            )
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise ForbiddenError("Not a member of this organization")

    org_result = await session.execute(
        select(Organization).where(Organization.id == member.organization_id)
    )
    org = org_result.scalar_one_or_none()
    if org is None:
        raise NotFoundError("Organization not found")
    return org, member
