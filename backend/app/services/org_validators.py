"""Organization-scoped entity validation helpers.

Enforces tenant isolation by verifying that referenced foreign objects
belong to the active organization before reading or writing.
Fails closed with NotFoundError to prevent cross-tenant existence enumeration.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.account import Account
from app.models.category import Category
from app.models.contact import Contact
from app.models.credit_card import CreditCard
from app.models.obligation import Obligation
from app.models.statement import Statement
from app.models.transaction import Transaction


async def validate_contact_in_org(
    session: AsyncSession,
    organization_id: UUID,
    contact_id: UUID,
) -> Contact:
    stmt = select(Contact).where(
        Contact.id == contact_id,
        Contact.organization_id == organization_id,
    )
    result = await session.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact is None:
        raise NotFoundError("Contact not found")
    return contact


async def validate_card_in_org(
    session: AsyncSession,
    organization_id: UUID,
    card_id: UUID,
) -> CreditCard:
    stmt = select(CreditCard).where(
        CreditCard.id == card_id,
        CreditCard.organization_id == organization_id,
    )
    result = await session.execute(stmt)
    card = result.scalar_one_or_none()
    if card is None:
        raise NotFoundError("Credit card not found")
    return card


async def validate_account_in_org(
    session: AsyncSession,
    organization_id: UUID,
    account_id: UUID,
) -> Account:
    stmt = select(Account).where(
        Account.id == account_id,
        Account.organization_id == organization_id,
    )
    result = await session.execute(stmt)
    account = result.scalar_one_or_none()
    if account is None:
        raise NotFoundError("Account not found")
    return account


async def validate_category_in_org(
    session: AsyncSession,
    organization_id: UUID,
    category_id: UUID,
) -> Category:
    stmt = select(Category).where(
        Category.id == category_id,
        Category.org_id == organization_id,
    )
    result = await session.execute(stmt)
    category = result.scalar_one_or_none()
    if category is None:
        raise NotFoundError("Category not found")
    return category


async def validate_transaction_in_org(
    session: AsyncSession,
    organization_id: UUID,
    transaction_id: UUID,
) -> Transaction:
    stmt = select(Transaction).where(
        Transaction.id == transaction_id,
        Transaction.organization_id == organization_id,
    )
    result = await session.execute(stmt)
    tx = result.scalar_one_or_none()
    if tx is None:
        raise NotFoundError("Transaction not found")
    return tx


async def validate_obligation_in_org(
    session: AsyncSession,
    organization_id: UUID,
    obligation_id: UUID,
) -> Obligation:
    stmt = select(Obligation).where(
        Obligation.id == obligation_id,
        Obligation.organization_id == organization_id,
    )
    result = await session.execute(stmt)
    ob = result.scalar_one_or_none()
    if ob is None:
        raise NotFoundError("Obligation not found")
    return ob


async def validate_statement_in_org(
    session: AsyncSession,
    organization_id: UUID,
    statement_id: UUID,
) -> Statement:
    stmt = select(Statement).where(
        Statement.id == statement_id,
        Statement.organization_id == organization_id,
    )
    result = await session.execute(stmt)
    st = result.scalar_one_or_none()
    if st is None:
        raise NotFoundError("Statement not found")
    return st
