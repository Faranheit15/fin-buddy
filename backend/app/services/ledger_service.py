"""Balance calculations for cards, contacts, and accounts — posted ledger only."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.domain.ledger import ASSET_EFFECT, CARD_EFFECT, CONTACT_EFFECT
from app.models.account import Account
from app.models.category import Category, CategoryKind
from app.models.enums import AccountKind, PostingStatus, TransactionType
from app.models.settlement import Settlement
from app.models.transaction import Transaction
from app.models.transaction_split import TransactionSplit

_OriginalTx = aliased(Transaction, name="tx_original")


def _posted_clause() -> Any:
    return Transaction.posting_status == PostingStatus.POSTED


def _effect_row_contribution_expr(effect_map: dict[TransactionType, int]) -> Any:
    """Per-row signed contribution using a type→multiplier map (paise)."""
    adjustment = Transaction.delta_sign * Transaction.amount_paise
    reversal = case(
        *(
            (_OriginalTx.type == t, -mult * Transaction.amount_paise)
            for t, mult in effect_map.items()
        ),
        else_=0,
    )
    return case(
        (Transaction.type == TransactionType.ADJUSTMENT, adjustment),
        (Transaction.type == TransactionType.REVERSAL, reversal),
        *(
            (Transaction.type == t, Transaction.amount_paise * mult)
            for t, mult in effect_map.items()
        ),
        else_=0,
    )


def _card_row_contribution_expr() -> Any:
    """Per-row signed contribution to card outstanding (paise)."""
    return _effect_row_contribution_expr(CARD_EFFECT)


def _asset_row_contribution_expr() -> Any:
    """Per-row signed contribution to asset cash held (paise)."""
    return _effect_row_contribution_expr(ASSET_EFFECT)


def _card_outstanding_expr() -> Any:
    return func.coalesce(func.sum(_card_row_contribution_expr()), 0)


def _account_row_contribution_expr() -> Any:
    """Kind-aware contribution: liability for credit_card, asset otherwise."""
    return case(
        (Account.kind == AccountKind.CREDIT_CARD, _card_row_contribution_expr()),
        else_=_asset_row_contribution_expr(),
    )


def _account_balance_sum_expr() -> Any:
    return func.coalesce(func.sum(_account_row_contribution_expr()), 0)


def _contact_row_contribution_expr() -> Any:
    """Per-row signed contribution to contact attributed spend (paise)."""
    return _effect_row_contribution_expr(CONTACT_EFFECT)


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


async def cards_outstanding_map(session: AsyncSession, organization_id: UUID) -> dict[UUID, int]:
    stmt = _with_original_join(
        select(Transaction.credit_card_id, _card_outstanding_expr()).where(
            and_(
                Transaction.organization_id == organization_id,
                _posted_clause(),
            )
        )
    ).group_by(Transaction.credit_card_id)
    result = await session.execute(stmt)
    return {row[0]: int(row[1] or 0) for row in result.all()}


async def account_balance_paise(session: AsyncSession, account_id: UUID) -> int:
    """Posted G2 balance for one account (outstanding or cash held by kind)."""
    stmt = _with_original_join(
        select(_account_balance_sum_expr())
        .select_from(Transaction)
        .join(Account, Account.id == Transaction.account_id)
        .where(and_(Transaction.account_id == account_id, _posted_clause()))
    )
    result = await session.execute(stmt)
    return int(result.scalar_one() or 0)


async def accounts_balances_map(session: AsyncSession, organization_id: UUID) -> dict[UUID, int]:
    """Per-account posted G2 balances for an org (missing keys → treat as 0)."""
    stmt = _with_original_join(
        select(Transaction.account_id, _account_balance_sum_expr())
        .select_from(Transaction)
        .join(Account, Account.id == Transaction.account_id)
        .where(
            and_(
                Transaction.organization_id == organization_id,
                Account.organization_id == organization_id,
                _posted_clause(),
            )
        )
    ).group_by(Transaction.account_id)
    result = await session.execute(stmt)
    return {row[0]: int(row[1] or 0) for row in result.all() if row[0] is not None}


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


async def contacts_balances_map(session: AsyncSession, organization_id: UUID) -> dict[UUID, int]:
    """Per-contact outstanding (posted spends − settlements) for an org."""
    spend_stmt = _with_original_join(
        select(Transaction.contact_id, _contact_spend_expr()).where(
            and_(
                Transaction.organization_id == organization_id,
                Transaction.contact_id.is_not(None),
                _posted_clause(),
            )
        )
    ).group_by(Transaction.contact_id)
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


async def income_expense_summary(
    session: AsyncSession,
    organization_id: UUID,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict[str, int]:
    """Returns total income and expense (excluding transfers, adjustments, reversals).

    If a transaction has splits, they should theoretically be aggregated.
    For a simplified summary, we sum the absolute value of tx amounts based on CategoryKind.
    Transactions without a category are assumed Expense if amount reduces asset, Income if increases,
    but for now we'll just sum where category is present, or fallback based on type.
    """
    # Exclude non-reporting types
    excluded_types = {
        TransactionType.TRANSFER_OUT,
        TransactionType.TRANSFER_IN,
        TransactionType.ADJUSTMENT,
        TransactionType.REVERSAL,
        TransactionType.OPENING_BALANCE,
    }

    tx_conditions = [
        Transaction.organization_id == organization_id,
        _posted_clause(),
        Transaction.type.not_in(excluded_types),
    ]
    if start_date:
        tx_conditions.append(Transaction.occurred_at >= start_date)
    if end_date:
        tx_conditions.append(Transaction.occurred_at <= end_date)

    # 1. Sum whole transactions that have a category
    tx_stmt = _with_original_join(
        select(Category.kind, func.sum(Transaction.amount_paise))
        .select_from(Transaction)
        .join(Category, Category.id == Transaction.category_id)
        .where(and_(*tx_conditions))
        .group_by(Category.kind)
    )

    split_conditions = [
        Transaction.organization_id == organization_id,
        Transaction.posting_status == PostingStatus.POSTED,
        Transaction.type.not_in(excluded_types),
    ]
    if start_date:
        split_conditions.append(Transaction.occurred_at >= start_date)
    if end_date:
        split_conditions.append(Transaction.occurred_at <= end_date)

    # 2. Sum splits
    split_stmt = (
        select(Category.kind, func.sum(TransactionSplit.amount_paise))
        .select_from(TransactionSplit)
        .join(Transaction, Transaction.id == TransactionSplit.transaction_id)
        .join(Category, Category.id == TransactionSplit.category_id)
        .where(and_(*split_conditions))
        .group_by(Category.kind)
    )

    tx_res = await session.execute(tx_stmt)
    split_res = await session.execute(split_stmt)

    summary = {"income": 0, "expense": 0}

    for kind, amount in tx_res.all():
        key = "income" if kind == CategoryKind.income else "expense"
        summary[key] += int(amount or 0)

    for kind, amount in split_res.all():
        key = "income" if kind == CategoryKind.income else "expense"
        summary[key] += int(amount or 0)

    return summary
