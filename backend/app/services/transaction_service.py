"""Auditable ledger transaction create / post / reverse / adjust."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.models.contact import Contact
from app.models.credit_card import CreditCard
from app.models.enums import ActivityAction, PostingStatus, TransactionType
from app.models.transaction import Transaction
from app.services.logging_service import log_activity

_CREATE_BLOCKED_TYPES = {TransactionType.ADJUSTMENT, TransactionType.REVERSAL}


async def create_transaction(
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID,
    credit_card_id: UUID,
    tx_type: TransactionType,
    amount_paise: int,
    occurred_at: datetime,
    merchant: str,
    contact_id: UUID | None = None,
    category: str | None = None,
    notes: str | None = None,
    currency: str = "INR",
    posting_status: PostingStatus = PostingStatus.POSTED,
    ip: str | None = None,
    ua: str | None = None,
) -> Transaction:
    if tx_type in _CREATE_BLOCKED_TYPES:
        raise AppError(
            "Use reverse or adjust endpoints for correction entries",
            code="invalid_posting_type",
        )
    await _ensure_card(db, organization_id, credit_card_id)
    if contact_id is not None:
        await _ensure_contact(db, organization_id, contact_id)

    tx = Transaction(
        id=uuid4(),
        organization_id=organization_id,
        credit_card_id=credit_card_id,
        contact_id=contact_id,
        type=tx_type,
        posting_status=posting_status,
        amount_paise=amount_paise,
        currency=currency,
        occurred_at=occurred_at,
        merchant=merchant,
        category=category,
        notes=notes,
        delta_sign=None,
        created_by=user_id,
    )
    db.add(tx)
    await log_activity(
        db,
        action=ActivityAction.TRANSACTION_CREATE,
        summary=(
            f"Transaction {tx_type.value} {amount_paise} paise @ {merchant} "
            f"({posting_status.value})"
        ),
        actor_user_id=user_id,
        organization_id=organization_id,
        resource_type="transaction",
        resource_id=str(tx.id),
        ip_address=ip,
        user_agent=ua,
        metadata={"posting_status": posting_status.value},
    )
    await db.flush()
    return tx


async def create_draft(
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID,
    **kwargs: Any,
) -> Transaction:
    return await create_transaction(
        db,
        organization_id=organization_id,
        user_id=user_id,
        posting_status=PostingStatus.DRAFT,
        **kwargs,
    )


async def post_draft(
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID,
    transaction_id: UUID,
    ip: str | None = None,
    ua: str | None = None,
) -> Transaction:
    tx = await get_transaction(db, organization_id, transaction_id)
    if tx.posting_status == PostingStatus.POSTED:
        raise ConflictError("Transaction is already posted", code="already_posted")
    if tx.posting_status != PostingStatus.DRAFT:
        raise AppError("Only draft transactions can be posted", code="not_draft")
    tx.posting_status = PostingStatus.POSTED
    await log_activity(
        db,
        action=ActivityAction.TRANSACTION_POST,
        summary=f"Posted draft transaction {tx.id}",
        actor_user_id=user_id,
        organization_id=organization_id,
        resource_type="transaction",
        resource_id=str(tx.id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.flush()
    return tx


async def update_transaction(
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID,
    transaction_id: UUID,
    patch: dict[str, Any],
    ip: str | None = None,
    ua: str | None = None,
) -> Transaction:
    tx = await get_transaction(db, organization_id, transaction_id)
    if tx.posting_status != PostingStatus.DRAFT:
        raise ConflictError(
            "Posted entries cannot be edited or deleted. Reverse instead.",
            code="posted_immutable",
        )
    if "type" in patch and patch["type"] in _CREATE_BLOCKED_TYPES:
        raise AppError(
            "Cannot set type to adjustment or reversal via update",
            code="invalid_posting_type",
        )
    if "contact_id" in patch and patch["contact_id"] is not None:
        await _ensure_contact(db, organization_id, patch["contact_id"])
    for key, value in patch.items():
        setattr(tx, key, value)
    await log_activity(
        db,
        action=ActivityAction.TRANSACTION_UPDATE,
        summary=f"Updated draft transaction {tx.id}",
        actor_user_id=user_id,
        organization_id=organization_id,
        resource_type="transaction",
        resource_id=str(tx.id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.flush()
    return tx


async def delete_transaction(
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID,
    transaction_id: UUID,
    ip: str | None = None,
    ua: str | None = None,
) -> None:
    tx = await get_transaction(db, organization_id, transaction_id)
    if tx.posting_status != PostingStatus.DRAFT:
        raise ConflictError(
            "Posted entries cannot be edited or deleted. Reverse instead.",
            code="posted_immutable",
        )
    await log_activity(
        db,
        action=ActivityAction.TRANSACTION_DELETE,
        summary=f"Deleted draft transaction {tx.id}",
        actor_user_id=user_id,
        organization_id=organization_id,
        resource_type="transaction",
        resource_id=str(tx.id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.delete(tx)
    await db.flush()


async def reverse_transaction(
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID,
    transaction_id: UUID,
    reason: str,
    occurred_at: datetime | None = None,
    ip: str | None = None,
    ua: str | None = None,
) -> Transaction:
    reason_clean = reason.strip()
    if not reason_clean:
        raise AppError("Reason is required", code="invalid_reason")

    original = await get_transaction(db, organization_id, transaction_id)
    if original.posting_status != PostingStatus.POSTED:
        raise AppError("Only posted transactions can be reversed", code="cannot_reverse")
    if original.type == TransactionType.REVERSAL:
        raise AppError("Cannot reverse a reversal entry", code="cannot_reverse")
    if original.reversed_by_id is not None:
        raise ConflictError("Transaction is already reversed", code="already_reversed")

    reversal = Transaction(
        id=uuid4(),
        organization_id=organization_id,
        credit_card_id=original.credit_card_id,
        contact_id=original.contact_id,
        type=TransactionType.REVERSAL,
        posting_status=PostingStatus.POSTED,
        amount_paise=original.amount_paise,
        currency=original.currency,
        occurred_at=occurred_at or datetime.now(UTC),
        merchant=f"Reversal of {original.merchant}"[:255],
        category=original.category,
        notes=None,
        correction_reason=reason_clean,
        delta_sign=None,
        reverses_id=original.id,
        created_by=user_id,
    )
    db.add(reversal)
    await db.flush()
    original.reversed_by_id = reversal.id
    await log_activity(
        db,
        action=ActivityAction.TRANSACTION_REVERSE,
        summary=f"Reversed transaction {original.id}",
        actor_user_id=user_id,
        organization_id=organization_id,
        resource_type="transaction",
        resource_id=str(reversal.id),
        ip_address=ip,
        user_agent=ua,
        metadata={"reverses_id": str(original.id), "reason": reason_clean},
    )
    await db.flush()
    return reversal


async def adjust_balance(
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID,
    credit_card_id: UUID,
    delta_paise: int,
    reason: str,
    contact_id: UUID | None = None,
    occurred_at: datetime | None = None,
    merchant: str | None = None,
    ip: str | None = None,
    ua: str | None = None,
) -> Transaction:
    if delta_paise == 0:
        raise AppError("delta_paise must be non-zero", code="invalid_delta")
    reason_clean = reason.strip()
    if not reason_clean:
        raise AppError("Reason is required", code="invalid_reason")

    await _ensure_card(db, organization_id, credit_card_id)
    if contact_id is not None:
        await _ensure_contact(db, organization_id, contact_id)

    amount = abs(delta_paise)
    sign = 1 if delta_paise > 0 else -1
    tx = Transaction(
        id=uuid4(),
        organization_id=organization_id,
        credit_card_id=credit_card_id,
        contact_id=contact_id,
        type=TransactionType.ADJUSTMENT,
        posting_status=PostingStatus.POSTED,
        amount_paise=amount,
        currency="INR",
        occurred_at=occurred_at or datetime.now(UTC),
        merchant=(merchant or "Balance adjustment")[:255],
        category=None,
        notes=None,
        correction_reason=reason_clean,
        delta_sign=sign,
        created_by=user_id,
    )
    db.add(tx)
    await log_activity(
        db,
        action=ActivityAction.TRANSACTION_ADJUST,
        summary=f"Adjustment {delta_paise} paise on card {credit_card_id}",
        actor_user_id=user_id,
        organization_id=organization_id,
        resource_type="transaction",
        resource_id=str(tx.id),
        ip_address=ip,
        user_agent=ua,
        metadata={"delta_paise": delta_paise, "reason": reason_clean},
    )
    await db.flush()
    return tx


async def get_transaction(
    db: AsyncSession, organization_id: UUID, transaction_id: UUID
) -> Transaction:
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.organization_id == organization_id,
        )
    )
    tx = result.scalar_one_or_none()
    if tx is None:
        raise NotFoundError("Transaction not found")
    return tx


async def _ensure_card(db: AsyncSession, org_id: UUID, card_id: UUID) -> None:
    result = await db.execute(
        select(CreditCard.id).where(CreditCard.id == card_id, CreditCard.organization_id == org_id)
    )
    if result.scalar_one_or_none() is None:
        raise NotFoundError("Credit card not found")


async def _ensure_contact(db: AsyncSession, org_id: UUID, contact_id: UUID) -> None:
    result = await db.execute(
        select(Contact.id).where(Contact.id == contact_id, Contact.organization_id == org_id)
    )
    if result.scalar_one_or_none() is None:
        raise NotFoundError("Contact not found")
