"""Balance calculations for cards and contacts — posted ledger rows only."""

from typing import Any
from uuid import UUID

from sqlalchemy import Select, and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.domain.ledger import CARD_EFFECT, CONTACT_EFFECT
from app.models.enums import PostingStatus, TransactionType
from app.models.settlement import Settlement
from app.models.transaction import Transaction

_OriginalTx = aliased(Transaction, name="tx_original")


def _posted_clause() -> Any:
    return Transaction.posting_status == PostingStatus.POSTED


def _card_row_contribution_expr() -> Any:
    """Per-row signed contribution to card outstanding (paise)."""
    adjustment = Transaction.delta_sign * Transaction.amount_paise
    reversal = case(
        *(
            (_OriginalTx.type == t, -mult * Transaction.amount_paise)
            for t, mult in CARD_EFFECT.items()
        ),
        else_=0,
    )
    return case(
        (Transaction.type == TransactionType.ADJUSTMENT, adjustment),
        (Transaction.type == TransactionType.REVERSAL, reversal),
        *(
            (Transaction.type == t, Transaction.amount_paise * mult)
            for t, mult in CARD_EFFECT.items()
        ),
        else_=0,
    )


def _card_outstanding_expr() -> Any:
    return func.coalesce(func.sum(_card_row_contribution_expr()), 0)


def _contact_row_contribution_expr() -> Any:
    """Per-row signed contribution to contact attributed spend (paise)."""
    adjustment = Transaction.delta_sign * Transaction.amount_paise
    reversal = case(
        *(
            (_OriginalTx.type == t, -mult * Transaction.amount_paise)
            for t, mult in CONTACT_EFFECT.items()
        ),
        else_=0,
    )
    return case(
        (Transaction.type == TransactionType.ADJUSTMENT, adjustment),
        (Transaction.type == TransactionType.REVERSAL, reversal),
        *(
            (Transaction.type == t, Transaction.amount_paise * mult)
            for t, mult in CONTACT_EFFECT.items()
        ),
        else_=0,
    )


def _contact_spend_expr() -> Any:
    return func.coalesce(func.sum(_contact_row_contribution_expr()), 0)


def _with_original_join(stmt: Any) -> Any:
    return stmt.outerjoin(_OriginalTx, Transaction.reverses_id == _OriginalTx.id)


async def card_outstanding_paise(session: AsyncSession, card_id: UUID) -> int:
    stmt = _with_original_join(
        select(_card_outstanding_expr()).where(
            and_(Transaction.credit_card_id == card_id, _posted_clause())
        )
    )
    result = await session.execute(stmt)
    return int(result.scalar_one() or 0)


async def cards_outstanding_map(
    session: AsyncSession, organization_id: UUID
) -> dict[UUID, int]:
    stmt = (
        _with_original_join(
            select(Transaction.credit_card_id, _card_outstanding_expr()).where(
                and_(
                    Transaction.organization_id == organization_id,
                    _posted_clause(),
                )
            )
        )
        .group_by(Transaction.credit_card_id)
    )
    result = await session.execute(stmt)
    return {row[0]: int(row[1] or 0) for row in result.all()}


async def contact_balance_paise(session: AsyncSession, contact_id: UUID) -> int:
    spend_stmt = _with_original_join(
        select(_contact_spend_expr()).where(
            and_(Transaction.contact_id == contact_id, _posted_clause())
        )
    )
    tx_result = await session.execute(spend_stmt)
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
    """Per-contact outstanding (posted spends − settlements) for an org."""
    spend_stmt = (
        _with_original_join(
            select(Transaction.contact_id, _contact_spend_expr()).where(
                and_(
                    Transaction.organization_id == organization_id,
                    Transaction.contact_id.is_not(None),
                    _posted_clause(),
                )
            )
        )
        .group_by(Transaction.contact_id)
    )
    spend_result = await session.execute(spend_stmt)
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
    """Sum of positive contact balances for an org (posted attributed spend − settlements)."""
    spend_stmt = _with_original_join(
        select(_contact_spend_expr()).where(
            and_(
                Transaction.organization_id == organization_id,
                Transaction.contact_id.is_not(None),
                _posted_clause(),
            )
        )
    )
    spend_result = await session.execute(spend_stmt)
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
