"""Read-only analytics used by the dashboard visualizations."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category, CategoryKind
from app.models.enums import PostingStatus, TransactionType
from app.models.transaction import Transaction
from app.models.transaction_split import TransactionSplit
from app.schemas.domain import DashboardCashFlowMonth, DashboardSpendCategory
from app.services.ledger_service import income_expense_summary

EXCLUDED_REPORTING_TYPES = {
    TransactionType.TRANSFER_OUT,
    TransactionType.TRANSFER_IN,
    TransactionType.ADJUSTMENT,
    TransactionType.REVERSAL,
    TransactionType.OPENING_BALANCE,
}
IST = ZoneInfo("Asia/Kolkata")


def _month_start(value: date) -> date:
    return value.replace(day=1)


def _prior_month(value: date) -> date:
    if value.month == 1:
        return value.replace(year=value.year - 1, month=12, day=1)
    return value.replace(month=value.month - 1, day=1)


def _month_starts(today: date, count: int = 6) -> list[date]:
    current = _month_start(today)
    months = [current]
    for _ in range(count - 1):
        months.append(_prior_month(months[-1]))
    return list(reversed(months))


async def cash_flow_trend(
    session: AsyncSession,
    *,
    organization_id: UUID,
    today: date,
) -> list[DashboardCashFlowMonth]:
    """Return six complete/current calendar months using ledger summary semantics."""
    result: list[DashboardCashFlowMonth] = []
    for month in _month_starts(today):
        start = datetime.combine(month, time.min, tzinfo=IST)
        following = date(month.year + (month.month == 12), month.month % 12 + 1, 1)
        end = datetime.combine(following, time.min, tzinfo=IST) - timedelta(microseconds=1)
        summary = await income_expense_summary(
            session,
            organization_id=organization_id,
            start_date=start,
            end_date=end,
        )
        result.append(
            DashboardCashFlowMonth(
                month=month,
                income_paise=summary["income"],
                expense_paise=summary["expense"],
            )
        )
    return result


async def spending_categories(
    session: AsyncSession,
    *,
    organization_id: UUID,
    start_of_month: datetime,
    limit: int = 5,
) -> list[DashboardSpendCategory]:
    """Return current-month expense categories, including split transactions."""
    common = [
        Transaction.organization_id == organization_id,
        Transaction.posting_status == PostingStatus.POSTED,
        Transaction.type.not_in(EXCLUDED_REPORTING_TYPES),
        Transaction.occurred_at >= start_of_month,
        Category.kind == CategoryKind.expense,
    ]
    has_splits = exists(
        select(TransactionSplit.id).where(TransactionSplit.transaction_id == Transaction.id)
    )
    whole_transactions = await session.execute(
        select(Category.name, Category.color, func.sum(Transaction.amount_paise))
        .select_from(Transaction)
        .join(Category, Category.id == Transaction.category_id)
        .where(*common, ~has_splits)
        .group_by(Category.name, Category.color)
    )
    split_transactions = await session.execute(
        select(Category.name, Category.color, func.sum(TransactionSplit.amount_paise))
        .select_from(TransactionSplit)
        .join(Transaction, Transaction.id == TransactionSplit.transaction_id)
        .join(Category, Category.id == TransactionSplit.category_id)
        .where(*common)
        .group_by(Category.name, Category.color)
    )

    totals: dict[tuple[str, str | None], int] = {}
    for name, color, amount in [*whole_transactions.all(), *split_transactions.all()]:
        key = (name, color)
        totals[key] = totals.get(key, 0) + int(amount or 0)

    return [
        DashboardSpendCategory(name=name, color=color, amount_paise=amount)
        for (name, color), amount in sorted(totals.items(), key=lambda item: item[1], reverse=True)[
            :limit
        ]
    ]
