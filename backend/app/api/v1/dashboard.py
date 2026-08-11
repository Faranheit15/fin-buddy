"""Dashboard aggregate endpoints."""

from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DbSession, OrgContext
from app.domain.billing import DueRuleType as DomainDueRuleType
from app.domain.billing import next_due_date_for_card, next_statement_date
from app.models.account import Account
from app.models.contact import Contact
from app.models.credit_card import CreditCard
from app.models.emi import EmiInstallment, EmiPlan
from app.models.enums import (
    AccountKind,
    CardStatus,
    EmiInstallmentStatus,
    EmiPlanStatus,
    ObligationStatus,
    ObligationType,
    StatementStatus,
)
from app.models.profile import Profile
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.schemas.domain import (
    AttentionItem,
    DashboardCardSummary,
    DashboardContactSummary,
    DashboardResponse,
)
from app.services import obligation_service
from app.services.dashboard_analytics import cash_flow_trend, spending_categories
from app.services.emi_service import cards_emi_blocked_map
from app.services.ledger_service import (
    accounts_balances_map,
    cards_outstanding_map,
    contacts_balances_map,
    income_expense_summary,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
IST = ZoneInfo("Asia/Kolkata")
TOP_CONTACTS_LIMIT = 8


@router.get("", response_model=DashboardResponse)
async def dashboard(
    db: DbSession,
    org_ctx: OrgContext,
    user: CurrentUser,
) -> DashboardResponse:
    org, _ = org_ctx
    today = datetime.now(IST).date()

    pref = await db.execute(
        select(Profile.due_soon_days, Profile.high_utilization_percent).where(Profile.id == user.id)
    )
    pref_row = pref.one_or_none()
    due_soon_days = pref_row[0] if pref_row else 7
    high_util_pct = pref_row[1] if pref_row else 80

    start_of_month_date = today.replace(day=1)
    from datetime import time

    start_of_month_dt = datetime.combine(start_of_month_date, time.min, tzinfo=IST)

    # One round-trip for the independent counters / sums.
    stats = await db.execute(
        select(
            select(func.coalesce(func.sum(CreditCard.credit_limit_paise), 0))
            .where(
                CreditCard.organization_id == org.id,
                CreditCard.status == CardStatus.ACTIVE,
            )
            .scalar_subquery(),
            select(func.count())
            .select_from(CreditCard)
            .where(CreditCard.organization_id == org.id)
            .scalar_subquery(),
            select(func.count())
            .select_from(Contact)
            .where(Contact.organization_id == org.id, Contact.archived_at.is_(None))
            .scalar_subquery(),
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.organization_id == org.id)
            .scalar_subquery(),
            select(func.count())
            .select_from(Statement)
            .where(
                Statement.organization_id == org.id,
                Statement.status == StatementStatus.NEEDS_REVIEW,
            )
            .scalar_subquery(),
        )
    )
    total_limit, cards_count, contacts_count, tx_count, review_count = stats.one()
    total_limit = int(total_limit or 0)

    outstanding_map = await cards_outstanding_map(db, org.id)
    emi_blocked_map = await cards_emi_blocked_map(db, org.id)
    balances = await contacts_balances_map(db, org.id)
    total_outstanding = sum(outstanding_map.values())
    friend_dues = sum(bal for bal in balances.values() if bal > 0)

    acc_bal_map = await accounts_balances_map(db, org.id)
    acc_result = await db.execute(select(Account).where(Account.organization_id == org.id))
    accounts = acc_result.scalars().all()

    bank_cash_wallet_sum = sum(
        acc_bal_map.get(acc.id, 0)
        for acc in accounts
        if acc.kind in (AccountKind.BANK, AccountKind.CASH, AccountKind.WALLET)
    )

    obligations = await obligation_service.list_obligations_with_balance(
        db, organization_id=org.id, status=ObligationStatus.ACTIVE
    )
    receivables_sum = sum(
        remaining for obl, remaining in obligations if obl.type == ObligationType.RECEIVABLE
    )
    payables_sum = sum(
        remaining for obl, remaining in obligations if obl.type == ObligationType.PAYABLE
    )

    assets_paise = bank_cash_wallet_sum + receivables_sum
    liabilities_paise = total_outstanding + payables_sum
    net_worth_paise = assets_paise - liabilities_paise

    period_summary = await income_expense_summary(
        db, organization_id=org.id, start_date=start_of_month_dt
    )
    period_income_paise = period_summary["income"]
    period_expense_paise = period_summary["expense"]
    cash_flow = await cash_flow_trend(db, organization_id=org.id, today=today)
    category_spend = await spending_categories(
        db,
        organization_id=org.id,
        start_of_month=start_of_month_dt,
    )

    result = await db.execute(
        select(CreditCard)
        .where(
            CreditCard.organization_id == org.id,
            CreditCard.status == CardStatus.ACTIVE,
        )
        .order_by(CreditCard.nickname.asc())
    )
    cards = list(result.scalars().all())
    card_summaries: list[DashboardCardSummary] = []
    attention: list[AttentionItem] = []

    # We will build upcoming_items dynamically, starting with Cards and EMIs.
    from app.schemas.domain import UpcomingItem

    upcoming_items: list[UpcomingItem] = []

    for card in cards:
        outstanding = outstanding_map.get(card.id, 0)
        emi_blocked = emi_blocked_map.get(card.id, 0)
        spend_outstanding = outstanding - emi_blocked
        available = max(card.credit_limit_paise - outstanding, 0)
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
        next_stmt = next_statement_date(today, card.statement_day)
        card_summaries.append(
            DashboardCardSummary(
                id=card.id,
                nickname=card.nickname,
                issuer=card.issuer,
                last_four=card.last_four,
                network=card.network,
                credit_limit_paise=card.credit_limit_paise,
                outstanding_paise=outstanding,
                spend_outstanding_paise=spend_outstanding,
                emi_principal_blocked_paise=emi_blocked,
                available_credit_paise=available,
                utilization_percent=util,
                next_due_date=next_due,
                next_statement_date=next_stmt,
                status=card.status,
            )
        )

        days_to_due = (next_due - today).days
        if days_to_due < 0:
            attention.append(
                AttentionItem(
                    id=f"due-{card.id}",
                    severity="critical",
                    title=f"{card.nickname} overdue",
                    detail=f"Payment was due {abs(days_to_due)}d ago · outstanding tracked",
                    href=f"/app/cards/{card.id}",
                )
            )
        elif days_to_due <= due_soon_days:
            attention.append(
                AttentionItem(
                    id=f"due-{card.id}",
                    severity="critical" if days_to_due <= 2 else "warning",
                    title=f"{card.nickname} due soon",
                    detail=f"Due in {days_to_due}d ({next_due.isoformat()})",
                    href=f"/app/cards/{card.id}",
                )
            )

        if days_to_due >= 0 and days_to_due <= due_soon_days:
            upcoming_items.append(
                UpcomingItem(
                    id=f"card-due-{card.id}",
                    type="card_due",
                    title=f"{card.nickname} Card Due",
                    amount_paise=outstanding,  # showing full outstanding
                    due_date=next_due,
                    href=f"/app/cards/{card.id}",
                )
            )

        if util >= high_util_pct:
            attention.append(
                AttentionItem(
                    id=f"util-{card.id}",
                    severity="critical" if util >= 90 else "warning",
                    title=f"{card.nickname} high utilization",
                    detail=f"{util}% of limit used",
                    href=f"/app/cards/{card.id}",
                )
            )

    if friend_dues > 0:
        attention.append(
            AttentionItem(
                id="friend-dues",
                severity="info",
                title="Friend balances open",
                detail="Tracked contact dues on your ledger",
                href="/app/contacts",
            )
        )

    if review_count:
        attention.append(
            AttentionItem(
                id="statements-review",
                severity="warning",
                title="Statements need review",
                detail=f"{int(review_count)} statement(s) ready for import review",
                href="/app/statements",
            )
        )

    top_contacts = await _top_contacts(db, org.id, balances)

    emi_result = await db.execute(
        select(EmiInstallment, EmiPlan)
        .join(EmiPlan, EmiInstallment.plan_id == EmiPlan.id)
        .where(
            EmiPlan.organization_id == org.id,
            EmiPlan.status == EmiPlanStatus.ACTIVE,
            EmiInstallment.status == EmiInstallmentStatus.PENDING,
        )
    )
    for inst, plan in emi_result.all():
        days_to_due = (inst.due_date - today).days
        if days_to_due <= due_soon_days:
            card_name = next((c.nickname for c in cards if c.id == plan.credit_card_id), "Card")
            upcoming_items.append(
                UpcomingItem(
                    id=f"emi-due-{inst.id}",
                    type="emi_due",
                    title=f"{card_name} EMI {inst.sequence_number}/{plan.tenure_months}",
                    amount_paise=inst.total_paise,
                    due_date=inst.due_date,
                    href=f"/app/cards/{plan.credit_card_id}",
                )
            )

    # Sort upcoming items by due date
    upcoming_items.sort(key=lambda x: x.due_date)

    # Add obligation dues to upcoming
    for obl, remaining in obligations:
        if obl.due_date and remaining > 0:
            days_to_due = (obl.due_date - today).days
            if 0 <= days_to_due <= due_soon_days:
                label = obl.counterparty_name or "Obligation"
                upcoming_items.append(
                    UpcomingItem(
                        id=f"obl-due-{obl.id}",
                        type="obligation_due",
                        title=f"{label} ({obl.type.value})",
                        amount_paise=remaining,
                        due_date=obl.due_date,
                        href=f"/app/debts/{obl.id}",
                    )
                )

    # Re-sort after adding obligations
    upcoming_items.sort(key=lambda x: x.due_date)

    return DashboardResponse(
        total_credit_limit_paise=total_limit,
        total_outstanding_paise=total_outstanding,
        total_available_credit_paise=max(total_limit - total_outstanding, 0),
        total_friend_dues_paise=friend_dues,
        net_worth_paise=net_worth_paise,
        assets_paise=assets_paise,
        liabilities_paise=liabilities_paise,
        period_income_paise=period_income_paise,
        period_expense_paise=period_expense_paise,
        cards_count=int(cards_count or 0),
        contacts_count=int(contacts_count or 0),
        transactions_count=int(tx_count or 0),
        attention=attention,
        upcoming_items=upcoming_items,
        cards=card_summaries,
        top_contacts=top_contacts,
        cash_flow_trend=cash_flow,
        spending_categories=category_spend,
    )


async def _top_contacts(
    db: AsyncSession,
    organization_id: UUID,
    balances: dict[UUID, int],
) -> list[DashboardContactSummary]:
    ranked = sorted(
        ((cid, bal) for cid, bal in balances.items() if bal > 0),
        key=lambda item: item[1],
        reverse=True,
    )[:TOP_CONTACTS_LIMIT]
    if not ranked:
        return []

    ids = [cid for cid, _ in ranked]
    result = await db.execute(
        select(Contact).where(
            Contact.organization_id == organization_id,
            Contact.id.in_(ids),
            Contact.archived_at.is_(None),
        )
    )
    by_id = {c.id: c for c in result.scalars().all()}
    return [
        DashboardContactSummary(
            id=cid,
            name=by_id[cid].name,
            outstanding_paise=bal,
            updated_at=by_id[cid].updated_at,
        )
        for cid, bal in ranked
        if cid in by_id
    ]
