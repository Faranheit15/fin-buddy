"""Background jobs and scheduled tasks endpoints."""

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import AppSettings, DbSession
from app.domain.billing import DueRuleType as DomainDueRuleType
from app.domain.billing import next_due_date_for_card
from app.models.credit_card import CreditCard
from app.models.emi import EmiInstallment, EmiPlan
from app.models.enums import CardStatus, EmiInstallmentStatus, EmiPlanStatus
from app.models.organization import Organization, OrganizationMember
from app.models.profile import Profile
from app.schemas.common import MessageResponse
from app.services.email_service import send_email
from app.services.ledger_service import cards_outstanding_map

router = APIRouter(prefix="/jobs", tags=["jobs"])
IST = ZoneInfo("Asia/Kolkata")


@router.post("/send-reminders", response_model=MessageResponse)
async def send_reminders(db: DbSession, settings: AppSettings) -> MessageResponse:
    """
    Trigger email reminders for all active profiles with reminders enabled.
    Typically called by a cron scheduler like GitHub Actions or a cloud scheduler.
    """
    profiles_result = await db.execute(
        select(Profile).where(
            Profile.is_active.is_(True),
            Profile.email_reminders_enabled.is_(True)
        )
    )
    profiles = profiles_result.scalars().all()
    today = datetime.now(IST).date()
    sent_count = 0

    for profile in profiles:
        if not profile.email:
            continue

        due_soon_days = profile.due_soon_days

        orgs_result = await db.execute(
            select(Organization.id)
            .join(OrganizationMember)
            .where(OrganizationMember.user_id == profile.id)
        )
        org_ids = [row[0] for row in orgs_result.all()]
        if not org_ids:
            continue

        reminders = []
        for org_id in org_ids:
            # 1. Cards Dues
            outstanding_map = await cards_outstanding_map(db, org_id)
            cards_result = await db.execute(
                select(CreditCard).where(
                    CreditCard.organization_id == org_id,
                    CreditCard.status == CardStatus.ACTIVE
                )
            )
            for card in cards_result.scalars().all():
                outstanding = outstanding_map.get(card.id, 0)
                if outstanding <= 0:
                    continue

                rule = DomainDueRuleType(card.due_rule_type.value)
                next_due = next_due_date_for_card(
                    today,
                    statement_day=card.statement_day,
                    due_rule_type=rule,
                    due_rule_value=card.due_rule_value,
                )

                days_to_due = (next_due - today).days
                if days_to_due <= due_soon_days:
                    amt = f"₹{outstanding / 100:,.2f}"
                    when = f"in {days_to_due} days" if days_to_due >= 0 else f"OVERDUE by {abs(days_to_due)} days"
                    if days_to_due == 0:
                        when = "TODAY"
                    reminders.append(f"• {card.nickname} Card: {amt} due {when} ({next_due})")

            # 2. EMIs Dues
            emi_result = await db.execute(
                select(EmiInstallment, EmiPlan, CreditCard)
                .join(EmiPlan, EmiInstallment.plan_id == EmiPlan.id)
                .join(CreditCard, EmiPlan.credit_card_id == CreditCard.id)
                .where(
                    EmiPlan.organization_id == org_id,
                    EmiPlan.status == EmiPlanStatus.ACTIVE,
                    EmiInstallment.status == EmiInstallmentStatus.PENDING,
                )
            )
            for inst, plan, card in emi_result.all():
                days_to_due = (inst.due_date - today).days
                if days_to_due <= due_soon_days:
                    amt = f"₹{inst.total_paise / 100:,.2f}"
                    when = f"in {days_to_due} days" if days_to_due >= 0 else f"OVERDUE by {abs(days_to_due)} days"
                    if days_to_due == 0:
                        when = "TODAY"
                    reminders.append(f"• {card.nickname} EMI ({inst.sequence_number}/{plan.tenure_months}): {amt} due {when} ({inst.due_date})")

        if reminders:
            # Sort just for better presentation if desired, but good enough as is.
            text_body = f"Hello {profile.display_name or 'User'},\n\nYou have upcoming or overdue items requiring your attention:\n\n"
            text_body += "\n".join(reminders)
            text_body += "\n\nLog in to Fin Buddy to manage these payments."
            await send_email(
                settings=settings,
                to_email=profile.email,
                subject="Fin Buddy: Upcoming Dues Reminder",
                text_body=text_body,
            )
            sent_count += 1

    return MessageResponse(message=f"Reminders sent to {sent_count} users")
