"""Balance calculations for cards and contacts."""

from typing import Any
from uuid import UUID

from sqlalchemy import Select, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TransactionType
from app.models.settlement import Settlement
from app.models.transaction import Transaction

# Effects on card outstanding (issuer liability)
_CARD_EFFECT = {
    TransactionType.PURCHASE: 1,
    TransactionType.FEE: 1,
    TransactionType.INTEREST: 1,
    TransactionType.OPENING_BALANCE: 1,
    TransactionType.REFUND: -1,
    TransactionType.PAYMENT_TO_ISSUER: -1,
}

# Effects on contact balance (what they owe the card owner)
_CONTACT_EFFECT = {
    TransactionType.PURCHASE: 1,
    TransactionType.FEE: 1,
    TransactionType.INTEREST: 1,
    TransactionType.OPENING_BALANCE: 0,  # typically self
    TransactionType.REFUND: -1,
    TransactionType.PAYMENT_TO_ISSUER: 0,
}


def _card_outstanding_expr() -> Any:
    return func.coalesce(
        func.sum(
            case(
                *(
                    (Transaction.type == t, Transaction.amount_paise * mult)
                    for t, mult in _CARD_EFFECT.items()
                ),
                else_=0,
            )
        ),
        0,
    )


async def card_outstanding_paise(session: AsyncSession, card_id: UUID) -> int:
    result = await session.execute(
        select(_card_outstanding_expr()).where(Transaction.credit_card_id == card_id)
    )
    return int(result.scalar_one() or 0)


async def cards_outstanding_map(
    session: AsyncSession, organization_id: UUID
) -> dict[UUID, int]:
    result = await session.execute(
        select(Transaction.credit_card_id, _card_outstanding_expr())
        .where(Transaction.organization_id == organization_id)
        .group_by(Transaction.credit_card_id)
    )
    return {row[0]: int(row[1] or 0) for row in result.all()}


def _contact_spend_expr() -> Any:
    return func.coalesce(
        func.sum(
            case(
                *(
                    (Transaction.type == t, Transaction.amount_paise * mult)
                    for t, mult in _CONTACT_EFFECT.items()
                ),
                else_=0,
            )
        ),
        0,
    )


async def contact_balance_paise(session: AsyncSession, contact_id: UUID) -> int:
    tx_result = await session.execute(
        select(_contact_spend_expr()).where(Transaction.contact_id == contact_id)
    )
    spends = int(tx_result.scalar_one() or 0)

    settle_result = await session.execute(
        select(func.coalesce(func.sum(Settlement.amount_paise), 0)).where(
            Settlement.contact_id == contact_id
        )
    )
    settlements = int(settle_result.scalar_one() or 0)
    return spends - settlements


async def contacts_balances_map(
    session: AsyncSession, organization_id: UUID
) -> dict[UUID, int]:
    """Per-contact outstanding (spends − settlements) for an org."""
    spend_result = await session.execute(
        select(Transaction.contact_id, _contact_spend_expr())
        .where(
            Transaction.organization_id == organization_id,
            Transaction.contact_id.is_not(None),
        )
        .group_by(Transaction.contact_id)
    )
    spends = {row[0]: int(row[1] or 0) for row in spend_result.all() if row[0] is not None}

    settle_result = await session.execute(
        select(
            Settlement.contact_id,
            func.coalesce(func.sum(Settlement.amount_paise), 0),
        )
        .where(Settlement.organization_id == organization_id)
        .group_by(Settlement.contact_id)
    )
    settlements = {row[0]: int(row[1] or 0) for row in settle_result.all()}

    contact_ids = set(spends) | set(settlements)
    return {cid: spends.get(cid, 0) - settlements.get(cid, 0) for cid in contact_ids}


async def total_friend_dues(session: AsyncSession, organization_id: UUID) -> int:
    """Sum of positive contact balances for an org (simple aggregation)."""
    # Compute per contact in SQL-ish way: total attributed spend effects - settlements
    spend_expr = func.coalesce(
        func.sum(
            case(
                *(
                    (Transaction.type == t, Transaction.amount_paise * mult)
                    for t, mult in _CONTACT_EFFECT.items()
                ),
                else_=0,
            )
        ),
        0,
    )
    spend_result = await session.execute(
        select(spend_expr).where(
            Transaction.organization_id == organization_id,
            Transaction.contact_id.is_not(None),
        )
    )
    spends = int(spend_result.scalar_one() or 0)
    settle_result = await session.execute(
        select(func.coalesce(func.sum(Settlement.amount_paise), 0)).where(
            Settlement.organization_id == organization_id
        )
    )
    settlements = int(settle_result.scalar_one() or 0)
    return max(spends - settlements, 0)


def base_org_query(model: type[object], organization_id: UUID) -> Select[tuple[object]]:
    return select(model).where(model.organization_id == organization_id)  # type: ignore[attr-defined]
