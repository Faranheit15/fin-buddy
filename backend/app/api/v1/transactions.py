"""Transaction ledger endpoints — draft/posted, reverse, adjust."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession, OrgContext, client_meta
from app.core.exceptions import AppError
from app.models.enums import PostingStatus, TransactionType
from app.models.transaction import Transaction
from app.schemas.common import PaginatedResponse
from app.schemas.domain import (
    TransactionAdjustRequest,
    TransactionCreate,
    TransactionResponse,
    TransactionReverseRequest,
    TransactionSplitBase,
    TransactionUpdate,
)
from app.services import account_service, transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=PaginatedResponse[TransactionResponse])
async def list_transactions(
    db: DbSession,
    org_ctx: OrgContext,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    card_id: UUID | None = None,
    contact_id: UUID | None = None,
    account_id: UUID | None = None,
    type: TransactionType | None = None,
    posting_status: PostingStatus | None = None,
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
    if account_id:
        filters.append(Transaction.account_id == account_id)
    if type:
        filters.append(Transaction.type == type)
    if posting_status:
        filters.append(Transaction.posting_status == posting_status)
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


@router.post("/adjust", response_model=TransactionResponse, status_code=201)
async def adjust_transaction(
    body: TransactionAdjustRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> TransactionResponse:
    org, _ = org_ctx
    ip, ua = client_meta(request)
    if body.account_id is not None:
        if body.contact_id is not None:
            raise AppError(
                "Account adjustments cannot include a contact", code="invalid_adjustment"
            )
        account = await account_service.get_account(
            db, organization_id=org.id, account_id=body.account_id
        )
        tx = await transaction_service.adjust_account_balance(
            db,
            organization_id=org.id,
            user_id=user.id,
            account=account,
            delta_paise=body.delta_paise,
            reason=body.reason,
            occurred_at=body.occurred_at,
            merchant=body.merchant,
            ip=ip,
            ua=ua,
        )
    else:
        if body.credit_card_id is None:
            raise AppError("account_id or credit_card_id is required", code="missing_account")
        tx = await transaction_service.adjust_balance(
            db,
            organization_id=org.id,
            user_id=user.id,
            credit_card_id=body.credit_card_id,
            delta_paise=body.delta_paise,
            reason=body.reason,
            contact_id=body.contact_id,
            occurred_at=body.occurred_at,
            merchant=body.merchant,
            ip=ip,
            ua=ua,
        )
    await db.commit()
    await db.refresh(tx)
    return TransactionResponse.model_validate(tx)


@router.post("", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    body: TransactionCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> TransactionResponse:
    org, _ = org_ctx
    ip, ua = client_meta(request)
    tx = await transaction_service.create_transaction(
        db,
        organization_id=org.id,
        user_id=user.id,
        account_id=body.account_id,
        credit_card_id=body.credit_card_id,
        tx_type=body.type,
        amount_paise=body.amount_paise,
        occurred_at=body.occurred_at,
        merchant=body.merchant,
        contact_id=body.contact_id,
        category_id=body.category_id,
        category=body.category,
        notes=body.notes,
        tags=body.tags,
        transfer_group_id=body.transfer_group_id,
        currency=body.currency,
        posting_status=body.posting_status,
        ip=ip,
        ua=ua,
    )
    await db.commit()
    await db.refresh(tx)
    return TransactionResponse.model_validate(tx)


@router.post("/{transaction_id}/post", response_model=TransactionResponse)
async def post_transaction(
    transaction_id: UUID,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> TransactionResponse:
    org, _ = org_ctx
    ip, ua = client_meta(request)
    tx = await transaction_service.post_draft(
        db,
        organization_id=org.id,
        user_id=user.id,
        transaction_id=transaction_id,
        ip=ip,
        ua=ua,
    )
    await db.commit()
    await db.refresh(tx)
    return TransactionResponse.model_validate(tx)


@router.post("/{transaction_id}/reverse", response_model=TransactionResponse, status_code=201)
async def reverse_transaction(
    transaction_id: UUID,
    body: TransactionReverseRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> TransactionResponse:
    org, _ = org_ctx
    ip, ua = client_meta(request)
    tx = await transaction_service.reverse_transaction(
        db,
        organization_id=org.id,
        user_id=user.id,
        transaction_id=transaction_id,
        reason=body.reason,
        occurred_at=body.occurred_at,
        ip=ip,
        ua=ua,
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
    ip, ua = client_meta(request)
    tx = await transaction_service.update_transaction(
        db,
        organization_id=org.id,
        user_id=user.id,
        transaction_id=transaction_id,
        patch=body.model_dump(exclude_unset=True),
        ip=ip,
        ua=ua,
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
    ip, ua = client_meta(request)
    await transaction_service.delete_transaction(
        db,
        organization_id=org.id,
        user_id=user.id,
        transaction_id=transaction_id,
        ip=ip,
        ua=ua,
    )
    await db.commit()


@router.put("/{transaction_id}/splits", response_model=TransactionResponse)
async def replace_transaction_splits(
    transaction_id: UUID,
    body: list[TransactionSplitBase],
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> TransactionResponse:
    org, _ = org_ctx
    ip, ua = client_meta(request)
    tx = await transaction_service.replace_transaction_splits(
        db,
        organization_id=org.id,
        user_id=user.id,
        transaction_id=transaction_id,
        splits_data=[s.model_dump(exclude_unset=True) for s in body],
        ip=ip,
        ua=ua,
    )
    await db.commit()
    await db.refresh(tx)
    return TransactionResponse.model_validate(tx)
