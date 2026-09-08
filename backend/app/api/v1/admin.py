"""Platform admin panel APIs — activity, errors, request logs, users."""

from uuid import UUID

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select

from app.api.deps import DbSession, PlatformAdmin, client_meta
from app.models.enums import ActivityAction, ErrorSeverity, PlatformRole
from app.models.logging import ActivityLog, ApiRequestLog, ErrorLog
from app.models.profile import Profile
from app.schemas.admin import (
    ActivityLogResponse,
    AdminUserResponse,
    ApiRequestLogResponse,
    ErrorLogResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.logging_service import log_activity

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/activity-logs", response_model=PaginatedResponse[ActivityLogResponse])
async def list_activity_logs(
    request: Request,
    db: DbSession,
    admin: PlatformAdmin,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    actor_user_id: UUID | None = None,
    action: ActivityAction | None = None,
) -> PaginatedResponse[ActivityLogResponse]:
    filters = []
    if actor_user_id:
        filters.append(ActivityLog.actor_user_id == actor_user_id)
    if action:
        filters.append(ActivityLog.action == action)

    total = await db.scalar(select(func.count()).select_from(ActivityLog).where(*filters)) or 0
    result = await db.execute(
        select(ActivityLog)
        .where(*filters)
        .order_by(ActivityLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.scalars().all()
    items = [
        ActivityLogResponse(
            id=r.id,
            actor_user_id=r.actor_user_id,
            organization_id=r.organization_id,
            action=r.action,
            resource_type=r.resource_type,
            resource_id=r.resource_id,
            summary=r.summary,
            metadata=r.metadata_json,
            ip_address=r.ip_address,
            user_agent=r.user_agent,
            created_at=r.created_at,
        )
        for r in rows
    ]
    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.ADMIN_VIEW,
        summary="Viewed activity logs",
        actor_user_id=admin.id,
        resource_type="activity_logs",
        ip_address=ip,
        user_agent=ua,
        commit=True,
    )
    return PaginatedResponse(items=items, total=int(total), page=page, page_size=page_size)


@router.get("/error-logs", response_model=PaginatedResponse[ErrorLogResponse])
async def list_error_logs(
    db: DbSession,
    admin: PlatformAdmin,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    severity: ErrorSeverity | None = None,
) -> PaginatedResponse[ErrorLogResponse]:
    _ = admin
    filters = []
    if severity:
        filters.append(ErrorLog.severity == severity)
    total = await db.scalar(select(func.count()).select_from(ErrorLog).where(*filters)) or 0
    result = await db.execute(
        select(ErrorLog)
        .where(*filters)
        .order_by(ErrorLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [ErrorLogResponse.model_validate(r) for r in result.scalars().all()]
    return PaginatedResponse(items=items, total=int(total), page=page, page_size=page_size)


@router.get("/request-logs", response_model=PaginatedResponse[ApiRequestLogResponse])
async def list_request_logs(
    db: DbSession,
    admin: PlatformAdmin,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status_code: int | None = None,
    path_contains: str | None = None,
) -> PaginatedResponse[ApiRequestLogResponse]:
    _ = admin
    filters = []
    if status_code is not None:
        filters.append(ApiRequestLog.status_code == status_code)
    if path_contains:
        filters.append(ApiRequestLog.path.ilike(f"%{path_contains}%"))
    total = await db.scalar(select(func.count()).select_from(ApiRequestLog).where(*filters)) or 0
    result = await db.execute(
        select(ApiRequestLog)
        .where(*filters)
        .order_by(ApiRequestLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [ApiRequestLogResponse.model_validate(r) for r in result.scalars().all()]
    return PaginatedResponse(items=items, total=int(total), page=page, page_size=page_size)


@router.get("/users", response_model=PaginatedResponse[AdminUserResponse])
async def list_users(
    db: DbSession,
    admin: PlatformAdmin,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedResponse[AdminUserResponse]:
    _ = admin
    total = await db.scalar(select(func.count()).select_from(Profile)) or 0
    result = await db.execute(
        select(Profile)
        .order_by(Profile.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [AdminUserResponse.model_validate(u) for u in result.scalars().all()]
    return PaginatedResponse(items=items, total=int(total), page=page, page_size=page_size)


@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
async def set_user_role(
    user_id: UUID,
    request: Request,
    db: DbSession,
    admin: PlatformAdmin,
    role: PlatformRole = Query(...),
) -> AdminUserResponse:
    if admin.platform_role != PlatformRole.SUPER_ADMIN:
        from app.core.exceptions import ForbiddenError

        raise ForbiddenError("Only super_admin can change platform roles")

    result = await db.execute(select(Profile).where(Profile.id == user_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("User not found")

    if profile.platform_role == PlatformRole.SUPER_ADMIN and role != PlatformRole.SUPER_ADMIN:
        super_admin_count = (
            await db.scalar(
                select(func.count())
                .select_from(Profile)
                .where(Profile.platform_role == PlatformRole.SUPER_ADMIN)
            )
            or 0
        )
        if super_admin_count <= 1:
            from app.core.exceptions import ForbiddenError

            raise ForbiddenError("Cannot demote the last remaining super_admin")

    profile.platform_role = role
    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.ADMIN_ACTION,
        summary=f"Set platform_role={role.value} for {user_id}",
        actor_user_id=admin.id,
        resource_type="profile",
        resource_id=str(user_id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.commit()
    await db.refresh(profile)
    return AdminUserResponse.model_validate(profile)
