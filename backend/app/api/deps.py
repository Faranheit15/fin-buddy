"""Shared FastAPI dependencies."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import ForbiddenError
from app.core.request_meta import client_ip as trusted_client_ip
from app.core.security import AuthUser, get_current_user, get_platform_admin
from app.db.session import get_db
from app.models.enums import OrgRole
from app.models.organization import Organization, OrganizationMember
from app.services.org_context import resolve_organization

DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[AuthUser, Depends(get_current_user)]
PlatformAdmin = Annotated[AuthUser, Depends(get_platform_admin)]
AppSettings = Annotated[Settings, Depends(get_settings)]


async def get_org_context(
    user: CurrentUser,
    db: DbSession,
    x_organization_id: Annotated[UUID | None, Header(alias="X-Organization-Id")] = None,
) -> tuple[Organization, OrganizationMember]:
    return await resolve_organization(db, user, x_organization_id)


OrgContext = Annotated[tuple[Organization, OrganizationMember], Depends(get_org_context)]


async def require_org_admin(
    org_ctx: OrgContext,
) -> tuple[Organization, OrganizationMember]:
    org, member = org_ctx
    if member.role not in (OrgRole.OWNER, OrgRole.ADMIN):
        raise ForbiddenError("This operation requires organization admin or owner authority")
    return org, member


OrgAdminContext = Annotated[tuple[Organization, OrganizationMember], Depends(require_org_admin)]


async def require_org_owner(
    org_ctx: OrgContext,
) -> tuple[Organization, OrganizationMember]:
    org, member = org_ctx
    if member.role != OrgRole.OWNER:
        raise ForbiddenError("This operation requires organization owner authority")
    return org, member


OrgOwnerContext = Annotated[tuple[Organization, OrganizationMember], Depends(require_org_owner)]


def client_meta(request: Request) -> tuple[str | None, str | None]:
    ip = trusted_client_ip(request)
    ua = request.headers.get("user-agent")
    return ip, ua
