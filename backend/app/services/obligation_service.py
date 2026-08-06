"""Obligation and obligation payment service."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.models.enums import ObligationStatus, ObligationType
from app.models.obligation import Obligation
from app.models.obligation_payment import ObligationPayment


async def create_obligation(
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID,
    type: ObligationType,
    amount_paise: int,
    currency: str = "INR",
    contact_id: UUID | None = None,
    counterparty_name: str | None = None,
    due_date: date | None = None,
    notes: str | None = None,
) -> Obligation:
    if amount_paise <= 0:
        raise AppError("Amount must be positive", code="invalid_amount")
    if contact_id is None and not counterparty_name:
        raise AppError(
            "Must provide either contact_id or counterparty_name", code="missing_counterparty"
        )

    obligation = Obligation(
        id=uuid4(),
        organization_id=organization_id,
        contact_id=contact_id,
        counterparty_name=counterparty_name,
        type=type,
        amount_paise=amount_paise,
        currency=currency,
        due_date=due_date,
        status=ObligationStatus.ACTIVE,
        notes=notes,
        created_by=user_id,
    )
    db.add(obligation)
    await db.flush()
    return obligation


async def get_obligation_with_balance(
    db: AsyncSession,
    *,
    organization_id: UUID,
    obligation_id: UUID,
) -> tuple[Obligation, int]:
    """Returns (Obligation, remaining_balance_paise)."""
    paid_sum = func.coalesce(func.sum(ObligationPayment.amount_paise), 0)

    stmt = (
        select(Obligation, paid_sum)
        .outerjoin(ObligationPayment, ObligationPayment.obligation_id == Obligation.id)
        .where(
            Obligation.id == obligation_id,
            Obligation.organization_id == organization_id,
        )
        .group_by(Obligation.id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if row is None:
        raise NotFoundError("Obligation not found")

    obligation, total_paid = row
    remaining = obligation.amount_paise - total_paid
    return obligation, remaining


async def list_obligations_with_balance(
    db: AsyncSession,
    *,
    organization_id: UUID,
    status: ObligationStatus | None = None,
    type: ObligationType | None = None,
    contact_id: UUID | None = None,
) -> list[tuple[Obligation, int]]:
    """Returns list of (Obligation, remaining_balance_paise)."""
    paid_sum = func.coalesce(func.sum(ObligationPayment.amount_paise), 0)

    stmt = (
        select(Obligation, paid_sum)
        .outerjoin(ObligationPayment, ObligationPayment.obligation_id == Obligation.id)
        .where(Obligation.organization_id == organization_id)
        .group_by(Obligation.id)
        .order_by(Obligation.created_at.desc())
    )

    if status is not None:
        stmt = stmt.where(Obligation.status == status)
    if type is not None:
        stmt = stmt.where(Obligation.type == type)
    if contact_id is not None:
        stmt = stmt.where(Obligation.contact_id == contact_id)

    result = await db.execute(stmt)
    rows = result.all()

    return [(obl, obl.amount_paise - paid) for obl, paid in rows]


async def update_obligation(
    db: AsyncSession,
    *,
    organization_id: UUID,
    obligation_id: UUID,
    status: ObligationStatus | None = None,
    due_date: date | None = None,
    notes: str | None = None,
) -> Obligation:
    obl, _ = await get_obligation_with_balance(
        db, organization_id=organization_id, obligation_id=obligation_id
    )
    if status is not None:
        obl.status = status
    if due_date is not None:
        obl.due_date = due_date
    if notes is not None:
        obl.notes = notes
    await db.flush()
    return obl


async def add_payment(
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID,
    obligation_id: UUID,
    amount_paise: int,
    date: datetime,
    account_id: UUID | None = None,
    notes: str | None = None,
) -> ObligationPayment:
    if amount_paise <= 0:
        raise AppError("Payment amount must be positive", code="invalid_amount")

    obl, remaining = await get_obligation_with_balance(
        db, organization_id=organization_id, obligation_id=obligation_id
    )

    # Overpayment policy: warn and allow.
    # The API layer will decide whether to emit a warning, but the service allows it.

    payment = ObligationPayment(
        id=uuid4(),
        organization_id=organization_id,
        obligation_id=obligation_id,
        account_id=account_id,
        amount_paise=amount_paise,
        date=date,
        notes=notes,
        created_by=user_id,
    )
    db.add(payment)

    # Automatically mark as PAID if remaining <= payment amount
    if remaining <= amount_paise and obl.status == ObligationStatus.ACTIVE:
        obl.status = ObligationStatus.PAID

    await db.flush()
    return payment


async def list_payments(
    db: AsyncSession,
    *,
    organization_id: UUID,
    obligation_id: UUID,
) -> list[ObligationPayment]:
    stmt = (
        select(ObligationPayment)
        .where(
            ObligationPayment.obligation_id == obligation_id,
            ObligationPayment.organization_id == organization_id,
        )
        .order_by(ObligationPayment.date.desc(), ObligationPayment.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
