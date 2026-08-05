"""Account helpers — resolve card accounts, Correct Balance."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.models.account import Account
from app.models.enums import AccountKind
from app.models.transaction import Transaction
from app.services.ledger_service import account_balance_paise


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

    Card create inserts accounts eagerly; this keeps existing writers
    safe after `account_id` became required.
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


async def get_account(
    db: AsyncSession,
    *,
    organization_id: UUID,
    account_id: UUID,
) -> Account:
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.organization_id == organization_id,
        )
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise NotFoundError("Account not found")
    return account


async def correct_balance(
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID,
    account_id: UUID,
    target_balance_paise: int,
    reason: str,
    occurred_at: datetime | None = None,
    ip: str | None = None,
    ua: str | None = None,
) -> Transaction:
    """Reconcile account to target via posted adjustment (server-side delta).

    `delta = target − current` using G2 `account_balance_paise`. Rejects archived
    accounts and zero delta (`already_at_target`).
    """
    account = await get_account(
        db, organization_id=organization_id, account_id=account_id
    )
    if account.archived_at is not None:
        raise AppError(
            "Cannot correct balance on an archived account",
            code="account_archived",
        )

    current = await account_balance_paise(db, account_id)
    delta = target_balance_paise - current
    if delta == 0:
        raise AppError(
            "Already at that balance",
            code="already_at_target",
        )

    # Lazy import avoids circular dependency with transaction_service.
    from app.services.transaction_service import adjust_account_balance

    return await adjust_account_balance(
        db,
        organization_id=organization_id,
        user_id=user_id,
        account=account,
        delta_paise=delta,
        reason=reason,
        occurred_at=occurred_at,
        merchant="Balance adjustment",
        ip=ip,
        ua=ua,
    )
