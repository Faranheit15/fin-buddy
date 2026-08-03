"""In-app notification listing, read state, and attention sync."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.billing import DueRuleType as DomainDueRuleType
from app.domain.billing import next_due_date_for_card
from app.models.credit_card import CreditCard
from app.models.enums import CardStatus, StatementStatus
from app.models.notification import InAppNotification
from app.models.statement import Statement
from app.services.ledger_service import cards_outstanding_map

IST = ZoneInfo("Asia/Kolkata")

# Types managed by attention sync (statement_ready is created at parse time).
SYNC_TYPES = frozenset({"overdue", "due_soon", "high_utilization", "friend_dues", "statement_review"})


@dataclass(frozen=True, slots=True)
class DesiredNotification:
    type: str
    title: str
    body: str
    href: str | None
    key: str  # stable key for dedupe (type + href or type)


async def list_notifications(
    db: AsyncSession,
    *,
    user_id: UUID,
    organization_id: UUID,
    unread_only: bool = False,
    limit: int = 50,
) -> list[InAppNotification]:
    filters = [
        InAppNotification.user_id == user_id,
        InAppNotification.organization_id == organization_id,
    ]
    if unread_only:
        filters.append(InAppNotification.read_at.is_(None))

    result = await db.execute(
        select(InAppNotification)
        .where(*filters)
        .order_by(InAppNotification.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def unread_count(
    db: AsyncSession,
    *,
    user_id: UUID,
    organization_id: UUID,
) -> int:
    count = await db.scalar(
        select(func.count())
        .select_from(InAppNotification)
        .where(
            InAppNotification.user_id == user_id,
            InAppNotification.organization_id == organization_id,
            InAppNotification.read_at.is_(None),
        )
    )
    return int(count or 0)


async def mark_read(
    db: AsyncSession,
    *,
    user_id: UUID,
    organization_id: UUID,
    notification_id: UUID,
) -> bool:
    result = await db.execute(
        select(InAppNotification).where(
            InAppNotification.id == notification_id,
            InAppNotification.user_id == user_id,
            InAppNotification.organization_id == organization_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return False
    if row.read_at is None:
        row.read_at = datetime.now(UTC)
    return True


async def mark_all_read(
    db: AsyncSession,
    *,
    user_id: UUID,
    organization_id: UUID,
) -> int:
    now = datetime.now(UTC)
    result = await db.execute(
        update(InAppNotification)
        .where(
            InAppNotification.user_id == user_id,
            InAppNotification.organization_id == organization_id,
            InAppNotification.read_at.is_(None),
        )
        .values(read_at=now)
        .returning(InAppNotification.id)
    )
    return len(result.all())


async def compute_desired_attention(
    db: AsyncSession,
    *,
    organization_id: UUID,
    due_soon_days: int = 7,
    high_utilization_percent: int = 80,
) -> list[DesiredNotification]:
    """Derive current attention items that should surface as in-app notifications."""
    today = datetime.now(IST).date()
    desired: list[DesiredNotification] = []

    outstanding_map = await cards_outstanding_map(db, organization_id)
    result = await db.execute(
        select(CreditCard).where(
            CreditCard.organization_id == organization_id,
            CreditCard.status == CardStatus.ACTIVE,
        )
    )
    cards = list(result.scalars().all())

    for card in cards:
        outstanding = outstanding_map.get(card.id, 0)
        util = (
            round((outstanding / card.credit_limit_paise) * 100, 1)
            if card.credit_limit_paise > 0
            else 0.0
        )
        rule = DomainDueRuleType(card.due_rule_type.value)
        next_due = next_due_date_for_card(
            today,
            statement_day=card.statement_day,
            due_rule_type=rule,
            due_rule_value=card.due_rule_value,
        )
        days_to_due = (next_due - today).days
        href = f"/app/cards/{card.id}"

        if days_to_due < 0:
            desired.append(
                DesiredNotification(
                    type="overdue",
                    title=f"{card.nickname} overdue",
                    body=f"Payment was due {abs(days_to_due)}d ago",
                    href=href,
                    key=f"overdue:{card.id}",
                )
            )
        elif days_to_due <= due_soon_days:
            desired.append(
                DesiredNotification(
                    type="due_soon",
                    title=f"{card.nickname} due soon",
                    body=f"Due in {days_to_due}d ({next_due.isoformat()})",
                    href=href,
                    key=f"due_soon:{card.id}",
                )
            )

        if util >= high_utilization_percent:
            desired.append(
                DesiredNotification(
                    type="high_utilization",
                    title=f"{card.nickname} high utilization",
                    body=f"{util}% of limit used",
                    href=href,
                    key=f"high_utilization:{card.id}",
                )
            )

    review_count = await db.scalar(
        select(func.count())
        .select_from(Statement)
        .where(
            Statement.organization_id == organization_id,
            Statement.status == StatementStatus.NEEDS_REVIEW,
        )
    )
    if review_count:
        desired.append(
            DesiredNotification(
                type="statement_review",
                title="Statements need review",
                body=f"{int(review_count)} statement(s) ready for import review",
                href="/app/statements",
                key="statement_review",
            )
        )

    return desired


async def sync_attention_notifications(
    db: AsyncSession,
    *,
    user_id: UUID,
    organization_id: UUID,
    due_soon_days: int = 7,
    high_utilization_percent: int = 80,
) -> int:
    """
    Upsert attention-based notifications for the current org state.

    - Creates unread rows for active conditions not already open.
    - Marks stale sync-managed unread rows as read when conditions clear.
    Returns number of newly created notifications.
    """
    desired = await compute_desired_attention(
        db,
        organization_id=organization_id,
        due_soon_days=due_soon_days,
        high_utilization_percent=high_utilization_percent,
    )
    desired_by_key = {d.key: d for d in desired}

    existing = await db.execute(
        select(InAppNotification).where(
            InAppNotification.user_id == user_id,
            InAppNotification.organization_id == organization_id,
            InAppNotification.type.in_(list(SYNC_TYPES)),
            InAppNotification.read_at.is_(None),
        )
    )
    open_rows = list(existing.scalars().all())

    def row_key(row: InAppNotification) -> str:
        # Prefer stable key from href when present (card-scoped).
        if row.href and row.href.startswith("/app/cards/"):
            card_id = row.href.rsplit("/", 1)[-1]
            return f"{row.type}:{card_id}"
        return row.type

    open_by_key = {row_key(r): r for r in open_rows}
    now = datetime.now(UTC)
    created = 0

    for key, item in desired_by_key.items():
        if key in open_by_key:
            # Refresh copy if still open
            row = open_by_key[key]
            row.title = item.title
            row.body = item.body
            row.href = item.href
            continue
        db.add(
            InAppNotification(
                id=uuid4(),
                organization_id=organization_id,
                user_id=user_id,
                type=item.type,
                title=item.title,
                body=item.body,
                href=item.href,
            )
        )
        created += 1

    for key, row in open_by_key.items():
        if key not in desired_by_key:
            row.read_at = now

    return created
