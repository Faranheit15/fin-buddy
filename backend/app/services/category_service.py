"""Category management and seeding defaults."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.category import Category, CategoryKind

DEFAULT_EXPENSE_CATEGORIES = [
    "Food & Dining",
    "Groceries",
    "Shopping",
    "Transport",
    "Utilities",
    "Housing",
    "Entertainment",
    "Health & Fitness",
    "Travel",
    "Subscriptions",
    "Personal Care",
    "Education",
    "EMI/Debt",
    "Miscellaneous",
]

DEFAULT_INCOME_CATEGORIES = [
    "Salary",
    "Business",
    "Investments",
    "Rental",
    "Gifts",
    "Refunds",
    "Other Income",
]


async def seed_default_categories(session: AsyncSession, org_id: UUID) -> None:
    """Seed the default income and expense categories for a new organization."""
    categories = []

    for name in DEFAULT_EXPENSE_CATEGORIES:
        categories.append(
            Category(
                org_id=org_id,
                name=name,
                kind=CategoryKind.expense,
            )
        )

    for name in DEFAULT_INCOME_CATEGORIES:
        categories.append(
            Category(
                org_id=org_id,
                name=name,
                kind=CategoryKind.income,
            )
        )

    session.add_all(categories)


async def get_categories(session: AsyncSession, org_id: UUID) -> list[Category]:
    result = await session.execute(
        select(Category)
        .where(Category.org_id == org_id, Category.archived_at.is_(None))
        .order_by(Category.name)
    )
    return list(result.scalars().all())


async def create_category(
    session: AsyncSession,
    org_id: UUID,
    name: str,
    kind: CategoryKind,
    color: str | None = None,
    icon: str | None = None,
) -> Category:
    # Optional: ensure unique name within kind?
    cat = Category(
        id=uuid4(),
        org_id=org_id,
        name=name,
        kind=kind,
        color=color,
        icon=icon,
    )
    session.add(cat)
    await session.flush()
    return cat


async def get_category(session: AsyncSession, org_id: UUID, category_id: UUID) -> Category:
    result = await session.execute(
        select(Category).where(Category.id == category_id, Category.org_id == org_id)
    )
    cat = result.scalar_one_or_none()
    if not cat:
        raise NotFoundError("Category not found")
    return cat


async def update_category(
    session: AsyncSession, org_id: UUID, category_id: UUID, patch: dict[str, Any]
) -> Category:
    cat = await get_category(session, org_id, category_id)
    if "archived" in patch:
        archived = patch.pop("archived")
        if archived and cat.archived_at is None:
            cat.archived_at = datetime.now(UTC)
        elif not archived and cat.archived_at is not None:
            cat.archived_at = None

    for key, value in patch.items():
        setattr(cat, key, value)

    await session.flush()
    return cat


async def delete_category(session: AsyncSession, org_id: UUID, category_id: UUID) -> None:
    cat = await get_category(session, org_id, category_id)
    # Just archive it instead of hard delete to avoid breaking historical txs
    cat.archived_at = datetime.now(UTC)
    await session.flush()
