"""Settlement endpoints."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession, OrgContext, client_meta
from app.core.exceptions import NotFoundError
from app.models.contact import Contact
from app.models.enums import ActivityAction
from app.models.settlement import Settlement
from app.schemas.common import PaginatedResponse
from app.schemas.domain import SettlementCreate, SettlementResponse
from app.services.logging_service import log_activity

router = APIRouter(prefix="/settlements", tags=["settlements"])


@router.get("", response_model=PaginatedResponse[SettlementResponse])
async def list_settlements(
    db: DbSession,
    org_ctx: OrgContext,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    contact_id: UUID | None = None,
) -> PaginatedResponse[SettlementResponse]:
    org, _ = org_ctx
    filters = [Settlement.organization_id == org.id]
    if contact_id:
        filters.append(Settlement.contact_id == contact_id)
    total = await db.scalar(select(func.count()).select_from(Settlement).where(*filters)) or 0
    result = await db.execute(
        select(Settlement)
        .where(*filters)
        .order_by(Settlement.settled_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [SettlementResponse.model_validate(s) for s in result.scalars().all()]
    return PaginatedResponse(items=items, total=int(total), page=page, page_size=page_size)


@router.post("", response_model=SettlementResponse, status_code=201)
async def create_settlement(
    body: SettlementCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> SettlementResponse:
    org, _ = org_ctx
    contact = await db.execute(
        select(Contact.id).where(Contact.id == body.contact_id, Contact.organization_id == org.id)
    )
    if contact.scalar_one_or_none() is None:
        raise NotFoundError("Contact not found")
    row = Settlement(
        id=uuid4(),
        organization_id=org.id,
        contact_id=body.contact_id,
        amount_paise=body.amount_paise,
        currency=body.currency,
        settled_at=body.settled_at,
        method=body.method,
        notes=body.notes,
        created_by=user.id,
    )
    db.add(row)
    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.SETTLEMENT_CREATE,
        summary=f"Settlement {body.amount_paise} paise from contact {body.contact_id}",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="settlement",
        resource_id=str(row.id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.commit()
    await db.refresh(row)
    return SettlementResponse.model_validate(row)


@router.delete("/{settlement_id}", status_code=204)
async def delete_settlement(
    settlement_id: UUID,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> None:
    org, _ = org_ctx
    result = await db.execute(
        select(Settlement).where(
            Settlement.id == settlement_id, Settlement.organization_id == org.id
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise NotFoundError("Settlement not found")
    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.SETTLEMENT_DELETE,
        summary=f"Deleted settlement {settlement_id}",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="settlement",
        resource_id=str(settlement_id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.delete(row)
    await db.commit()
