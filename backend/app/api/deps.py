"""Shared FastAPI dependencies."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import AuthUser, get_current_user, get_platform_admin
from app.db.session import get_db
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


def client_meta(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    ua = request.headers.get("user-agent")
    return ip, ua
