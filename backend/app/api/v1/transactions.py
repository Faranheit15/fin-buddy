"""Transaction ledger endpoints."""

from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession, OrgContext, client_meta
from app.core.exceptions import NotFoundError
from app.models.contact import Contact
from app.models.credit_card import CreditCard
from app.models.enums import ActivityAction, TransactionType
from app.models.transaction import Transaction
from app.schemas.common import PaginatedResponse
from app.schemas.domain import TransactionCreate, TransactionResponse, TransactionUpdate
from app.services.logging_service import log_activity

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=PaginatedResponse[TransactionResponse])
async def list_transactions(
    db: DbSession,
    org_ctx: OrgContext,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    card_id: UUID | None = None,
    contact_id: UUID | None = None,
    type: TransactionType | None = None,
    q: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> PaginatedResponse[TransactionResponse]:
    org, _ = org_ctx
    filters = [Transaction.organization_id == org.id]
    if card_id:
        filters.append(Transaction.credit_card_id == card_id)
    if contact_id:
        filters.append(Transaction.contact_id == contact_id)
    if type:
        filters.append(Transaction.type == type)
    if date_from:
        filters.append(Transaction.occurred_at >= date_from)
    if date_to:
        filters.append(Transaction.occurred_at <= date_to)
    if q:
        filters.append(Transaction.merchant.ilike(f"%{q}%"))

    total = await db.scalar(select(func.count()).select_from(Transaction).where(*filters)) or 0
    result = await db.execute(
        select(Transaction)
        .where(*filters)
        .order_by(Transaction.occurred_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [TransactionResponse.model_validate(t) for t in result.scalars().all()]
    return PaginatedResponse(items=items, total=int(total), page=page, page_size=page_size)


@router.post("", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    body: TransactionCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> TransactionResponse:
    org, _ = org_ctx
    await _ensure_card(db, org.id, body.credit_card_id)
    if body.contact_id is not None:
        await _ensure_contact(db, org.id, body.contact_id)
    tx = Transaction(
        id=uuid4(),
        organization_id=org.id,
        credit_card_id=body.credit_card_id,
        contact_id=body.contact_id,
        type=body.type,
        amount_paise=body.amount_paise,
        currency=body.currency,
        occurred_at=body.occurred_at,
        merchant=body.merchant,
        category=body.category,
        notes=body.notes,
        created_by=user.id,
    )
    db.add(tx)
    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.TRANSACTION_CREATE,
        summary=f"Transaction {body.type.value} {body.amount_paise} paise @ {body.merchant}",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="transaction",
        resource_id=str(tx.id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.commit()
    await db.refresh(tx)
    return TransactionResponse.model_validate(tx)


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    body: TransactionUpdate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> TransactionResponse:
    org, _ = org_ctx
    tx = await _get(db, org.id, transaction_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(tx, key, value)
    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.TRANSACTION_UPDATE,
        summary=f"Updated transaction {tx.id}",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="transaction",
        resource_id=str(tx.id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.commit()
    await db.refresh(tx)
    return TransactionResponse.model_validate(tx)


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: UUID,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> None:
    org, _ = org_ctx
    tx = await _get(db, org.id, transaction_id)
    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.TRANSACTION_DELETE,
        summary=f"Deleted transaction {tx.id}",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="transaction",
        resource_id=str(tx.id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.delete(tx)
    await db.commit()


async def _get(db: DbSession, org_id: UUID, tx_id: UUID) -> Transaction:
    result = await db.execute(
        select(Transaction).where(Transaction.id == tx_id, Transaction.organization_id == org_id)
    )
    tx = result.scalar_one_or_none()
    if tx is None:
        raise NotFoundError("Transaction not found")
    return tx


async def _ensure_card(db: DbSession, org_id: UUID, card_id: UUID) -> None:
    result = await db.execute(
        select(CreditCard.id).where(CreditCard.id == card_id, CreditCard.organization_id == org_id)
    )
    if result.scalar_one_or_none() is None:
        raise NotFoundError("Credit card not found")


async def _ensure_contact(db: DbSession, org_id: UUID, contact_id: UUID) -> None:
    result = await db.execute(
        select(Contact.id).where(Contact.id == contact_id, Contact.organization_id == org_id)
    )
    if result.scalar_one_or_none() is None:
        raise NotFoundError("Contact not found")
