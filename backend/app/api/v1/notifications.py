"""In-app notifications (list, unread count, mark read)."""

from uuid import UUID

from fastapi import APIRouter, Query, Request
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, OrgContext, client_meta
from app.core.exceptions import NotFoundError
from app.models.enums import ActivityAction
from app.models.profile import Profile
from app.schemas.common import PaginatedResponse
from app.schemas.domain import (
    NotificationMarkReadResult,
    NotificationResponse,
    NotificationUnreadCount,
)
from app.services import notification_service
from app.services.logging_service import log_activity

router = APIRouter(prefix="/notifications", tags=["notifications"])


async def _profile_prefs(db: DbSession, user_id: UUID) -> tuple[int, int]:
    result = await db.execute(select(Profile).where(Profile.id == user_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        return 7, 80
    return profile.due_soon_days, profile.high_utilization_percent


@router.get("", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    sync: bool = Query(True, description="Refresh due/utilization notifications before list"),
) -> PaginatedResponse[NotificationResponse]:
    org, _ = org_ctx
    if sync:
        due_days, util_pct = await _profile_prefs(db, user.id)
        await notification_service.sync_attention_notifications(
            db,
            user_id=user.id,
            organization_id=org.id,
            due_soon_days=due_days,
            high_utilization_percent=util_pct,
        )
        await db.commit()

    items = await notification_service.list_notifications(
        db,
        user_id=user.id,
        organization_id=org.id,
        unread_only=unread_only,
        limit=page_size,
    )
    # Simple page: first page only for v1 (ordered newest first, capped).
    # Total reflects returned window for personal use; full count is overkill.
    total = len(items)
    if page > 1:
        items = []
    return PaginatedResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/unread-count", response_model=NotificationUnreadCount)
async def get_unread_count(
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
    sync: bool = Query(False),
) -> NotificationUnreadCount:
    org, _ = org_ctx
    if sync:
        due_days, util_pct = await _profile_prefs(db, user.id)
        await notification_service.sync_attention_notifications(
            db,
            user_id=user.id,
            organization_id=org.id,
            due_soon_days=due_days,
            high_utilization_percent=util_pct,
        )
        await db.commit()
    count = await notification_service.unread_count(db, user_id=user.id, organization_id=org.id)
    return NotificationUnreadCount(unread=count)


@router.post("/read-all", response_model=NotificationMarkReadResult)
async def mark_all_notifications_read(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> NotificationMarkReadResult:
    org, _ = org_ctx
    updated = await notification_service.mark_all_read(db, user_id=user.id, organization_id=org.id)
    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.NOTIFICATION_READ,
        summary=f"Marked {updated} notifications read",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="notification",
        ip_address=ip,
        user_agent=ua,
        metadata={"updated": updated},
    )
    await db.commit()
    return NotificationMarkReadResult(updated=updated)


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> NotificationResponse:
    org, _ = org_ctx
    ok = await notification_service.mark_read(
        db,
        user_id=user.id,
        organization_id=org.id,
        notification_id=notification_id,
    )
    if not ok:
        raise NotFoundError("Notification not found")

    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.NOTIFICATION_READ,
        summary="Marked notification read",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="notification",
        resource_id=str(notification_id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.commit()

    from sqlalchemy import select

    from app.models.notification import InAppNotification

    result = await db.execute(
        select(InAppNotification).where(
            InAppNotification.id == notification_id,
            InAppNotification.user_id == user.id,
            InAppNotification.organization_id == org.id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise NotFoundError("Notification not found")
    return NotificationResponse.model_validate(row)
