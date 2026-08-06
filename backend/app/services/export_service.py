"""Export service."""

from __future__ import annotations

import io
from uuid import UUID

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.contact import Contact
from app.models.credit_card import CreditCard
from app.models.obligation import Obligation
from app.models.transaction import Transaction


async def generate_org_export(db: AsyncSession, org_id: UUID) -> bytes:
    """Generate an Excel workbook with core organization data."""
    
    # 1. Accounts
    accounts_res = await db.execute(
        select(Account)
        .where(Account.organization_id == org_id)
        .order_by(Account.created_at)
    )
    accounts = accounts_res.scalars().all()
    accounts_data = [
        {
            "ID": str(a.id),
            "Name": a.name,
            "Kind": a.kind.value,
            "Institution": a.institution or "",
            "Currency": a.currency,
        }
        for a in accounts
    ]
    
    # 2. Transactions
    # For now, just raw transactions. If we had balances we would include them, but balance is computed.
    tx_res = await db.execute(
        select(Transaction)
        .where(Transaction.organization_id == org_id)
        .order_by(Transaction.occurred_at.desc(), Transaction.created_at.desc())
    )
    transactions = tx_res.scalars().all()
    transactions_data = [
        {
            "ID": str(t.id),
            "Date": t.occurred_at.strftime("%Y-%m-%d %H:%M:%S") if t.occurred_at else "",
            "Amount (Paise)": t.amount_paise,
            "Type": t.type.value,
            "Posting Status": t.posting_status.value,
            "Merchant/Description": t.merchant,
            "Category": t.category or "",
            "Account ID": str(t.account_id) if t.account_id else "",
            "Contact ID": str(t.contact_id) if t.contact_id else "",
            "Notes": t.notes or "",
        }
        for t in transactions
    ]
    
    # 3. Contacts
    contacts_res = await db.execute(
        select(Contact)
        .where(Contact.organization_id == org_id)
        .order_by(Contact.name)
    )
    contacts = contacts_res.scalars().all()
    contacts_data = [
        {
            "ID": str(c.id),
            "Name": c.name,
            "Email": c.email or "",
            "Phone": c.phone or "",
            "Archived": c.archived_at is not None,
        }
        for c in contacts
    ]
    
    # 4. Obligations
    ob_res = await db.execute(
        select(Obligation)
        .where(Obligation.organization_id == org_id)
        .order_by(Obligation.created_at.desc())
    )
    obligations = ob_res.scalars().all()
    obligations_data = [
        {
            "ID": str(o.id),
            "Type": o.type.value,
            "Amount (Paise)": o.amount_paise,
            "Status": o.status.value,
            "Contact ID": str(o.contact_id) if o.contact_id else "",
            "Counterparty": o.counterparty_name or "",
            "Notes": o.notes or "",
        }
        for o in obligations
    ]
    
    # 5. Cards
    cards_res = await db.execute(
        select(CreditCard)
        .where(CreditCard.organization_id == org_id)
        .order_by(CreditCard.created_at)
    )
    cards = cards_res.scalars().all()
    cards_data = [
        {
            "ID": str(c.id),
            "Nickname": c.nickname,
            "Issuer": c.issuer,
            "Network": c.network.value if c.network else "",
            "Last 4": c.last_four,
            "Credit Limit (Paise)": c.credit_limit_paise,
            "Status": c.status.value,
        }
        for c in cards
    ]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(accounts_data).to_excel(writer, sheet_name="Accounts", index=False)
        pd.DataFrame(transactions_data).to_excel(writer, sheet_name="Transactions", index=False)
        pd.DataFrame(contacts_data).to_excel(writer, sheet_name="Contacts", index=False)
        pd.DataFrame(obligations_data).to_excel(writer, sheet_name="Obligations", index=False)
        pd.DataFrame(cards_data).to_excel(writer, sheet_name="Cards", index=False)
    
    return output.getvalue()
