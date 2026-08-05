"""Account helpers — resolve/create card-linked accounts for ledger writers."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.enums import AccountKind


async def resolve_account_id_for_card(
    db: AsyncSession,
    *,
    organization_id: UUID,
    credit_card_id: UUID,
    name: str = "Card",
    institution: str | None = None,
    currency: str = "INR",
) -> UUID:
    """Return the 1:1 credit_card account id, creating it if missing.

    Card create (I3) will insert accounts eagerly; this keeps existing writers
    and pre-migration runtimes safe after `account_id` became required.
    """
    result = await db.execute(
        select(Account.id).where(
            Account.credit_card_id == credit_card_id,
            Account.organization_id == organization_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing

    account = Account(
        id=uuid4(),
        organization_id=organization_id,
        kind=AccountKind.CREDIT_CARD,
        name=name[:120],
        institution=institution,
        currency=currency,
        credit_card_id=credit_card_id,
    )
    db.add(account)
    await db.flush()
    return account.id
