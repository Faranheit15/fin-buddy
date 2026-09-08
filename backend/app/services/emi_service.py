"""Service for managing EMIs."""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from dateutil.relativedelta import relativedelta  # type: ignore
from sqlalchemy import func, select

from app.api.deps import DbSession
from app.core.exceptions import AppError
from app.models.emi import EmiInstallment, EmiPlan
from app.models.enums import EmiInstallmentStatus, EmiPlanStatus
from app.services.org_validators import validate_card_in_org, validate_transaction_in_org


def generate_emi_schedule(
    principal_paise: int,
    interest_rate_bps: int,
    tenure_months: int,
    start_date: date,
) -> list[EmiInstallment]:
    """
    Generate an EMI schedule.

    Args:
        principal_paise: Total principal amount in paise.
        interest_rate_bps: Annual interest rate in basis points (e.g. 1500 for 15%).
        tenure_months: Number of months for the EMI.
        start_date: The date of the first installment.

    Returns:
        List of EmiInstallment objects (without plan_id/id bound).
    """
    if tenure_months <= 0:
        raise ValueError("Tenure must be at least 1 month")

    # Standard reducing balance EMI formula:
    # EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
    # where P = principal, r = monthly interest rate, n = tenure

    monthly_rate = Decimal(interest_rate_bps) / Decimal(10000) / Decimal(12)
    principal = Decimal(principal_paise)
    n = tenure_months

    if monthly_rate > 0:
        factor = (1 + monthly_rate) ** n
        emi_amount = principal * monthly_rate * factor / (factor - 1)
    else:
        emi_amount = principal / n

    # We round the EMI amount to the nearest paise
    emi_amount_paise = int(emi_amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    installments = []
    remaining_principal = principal

    for month in range(1, tenure_months + 1):
        due_date = start_date + relativedelta(months=month - 1)

        interest_for_month = remaining_principal * monthly_rate
        interest_paise = int(interest_for_month.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

        # GST is 18% on interest
        gst_for_month = Decimal(interest_paise) * Decimal("0.18")
        gst_paise = int(gst_for_month.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

        if month == tenure_months:
            # Last month absorbs remainder
            principal_for_month = int(remaining_principal)
        else:
            principal_for_month = emi_amount_paise - interest_paise

        remaining_principal -= Decimal(principal_for_month)
        total_installment = principal_for_month + interest_paise + gst_paise

        installment = EmiInstallment(
            sequence_number=month,
            due_date=due_date,
            principal_paise=principal_for_month,
            interest_paise=interest_paise,
            fees_paise=0,
            gst_paise=gst_paise,
            total_paise=total_installment,
            status=EmiInstallmentStatus.PENDING,
        )
        installments.append(installment)

    return installments


async def card_emi_blocked_paise(
    db: DbSession, credit_card_id: UUID, organization_id: UUID | None = None
) -> int:
    """Get the sum of pending principal for all active EMIs on a card."""
    filters = [
        EmiPlan.credit_card_id == credit_card_id,
        EmiPlan.status == EmiPlanStatus.ACTIVE,
        EmiInstallment.status == EmiInstallmentStatus.PENDING,
    ]
    if organization_id is not None:
        filters.append(EmiPlan.organization_id == organization_id)

    result = await db.scalar(
        select(func.sum(EmiInstallment.principal_paise))
        .join(EmiPlan, EmiInstallment.plan_id == EmiPlan.id)
        .where(*filters)
    )
    return int(result or 0)


async def cards_emi_blocked_map(db: DbSession, organization_id: UUID) -> dict[UUID, int]:
    """Get a map of card_id -> pending emi principal for an organization."""
    result = await db.execute(
        select(EmiPlan.credit_card_id, func.sum(EmiInstallment.principal_paise))
        .join(EmiInstallment, EmiInstallment.plan_id == EmiPlan.id)
        .where(
            EmiPlan.organization_id == organization_id,
            EmiPlan.status == EmiPlanStatus.ACTIVE,
            EmiInstallment.status == EmiInstallmentStatus.PENDING,
        )
        .group_by(EmiPlan.credit_card_id)
    )
    return {row[0]: int(row[1] or 0) for row in result.all()}


async def create_emi_plan(
    db: DbSession,
    *,
    organization_id: UUID,
    credit_card_id: UUID,
    reference_transaction_id: UUID | None = None,
    principal_paise: int,
    interest_rate_bps: int,
    tenure_months: int,
    start_date: date,
) -> EmiPlan:
    from uuid import uuid4

    await validate_card_in_org(db, organization_id, credit_card_id)
    if reference_transaction_id is not None:
        ref_tx = await validate_transaction_in_org(
            db, organization_id, reference_transaction_id
        )
        if ref_tx.credit_card_id != credit_card_id:
            raise AppError(
                "Reference transaction does not belong to the selected credit card",
                code="card_tx_mismatch",
            )

    installments = generate_emi_schedule(
        principal_paise=principal_paise,
        interest_rate_bps=interest_rate_bps,
        tenure_months=tenure_months,
        start_date=start_date,
    )

    plan = EmiPlan(
        id=uuid4(),
        organization_id=organization_id,
        credit_card_id=credit_card_id,
        reference_transaction_id=reference_transaction_id,
        principal_paise=principal_paise,
        interest_rate_bps=interest_rate_bps,
        tenure_months=tenure_months,
        status=EmiPlanStatus.ACTIVE,
    )
    db.add(plan)
    await db.flush()

    for inst in installments:
        inst.id = uuid4()
        inst.plan_id = plan.id
        db.add(inst)

    await db.flush()
    # Eagerly load installments to return
    await db.refresh(plan, ["installments"])
    return plan


async def pay_emi_installment(
    db: DbSession,
    *,
    organization_id: UUID,
    user_id: UUID,
    installment_id: UUID,
    ip: str | None = None,
    ua: str | None = None,
) -> EmiInstallment:
    from datetime import UTC, datetime, time

    from app.core.exceptions import ConflictError, NotFoundError
    from app.models.enums import PostingStatus, TransactionType
    from app.services.transaction_service import create_transaction

    result = await db.execute(
        select(EmiInstallment, EmiPlan)
        .join(EmiPlan, EmiInstallment.plan_id == EmiPlan.id)
        .where(
            EmiInstallment.id == installment_id,
            EmiPlan.organization_id == organization_id,
        )
        .with_for_update(of=EmiInstallment)
    )
    row = result.first()
    if not row:
        raise NotFoundError("Installment not found")

    inst: EmiInstallment = row[0]
    plan: EmiPlan = row[1]

    if inst.status == EmiInstallmentStatus.PAID:
        raise ConflictError("Installment is already paid", code="installment_already_paid")

    occurred_at = datetime.combine(inst.due_date, time.min, tzinfo=UTC)

    if inst.interest_paise > 0:
        await create_transaction(
            db,
            organization_id=organization_id,
            user_id=user_id,
            credit_card_id=plan.credit_card_id,
            tx_type=TransactionType.EMI_INTEREST,
            amount_paise=inst.interest_paise,
            occurred_at=occurred_at,
            merchant=f"EMI Interest - Month {inst.sequence_number}/{plan.tenure_months}",
            posting_status=PostingStatus.POSTED,
            ip=ip,
            ua=ua,
        )

    if inst.gst_paise > 0:
        await create_transaction(
            db,
            organization_id=organization_id,
            user_id=user_id,
            credit_card_id=plan.credit_card_id,
            tx_type=TransactionType.EMI_GST,
            amount_paise=inst.gst_paise,
            occurred_at=occurred_at,
            merchant=f"EMI GST - Month {inst.sequence_number}/{plan.tenure_months}",
            posting_status=PostingStatus.POSTED,
            ip=ip,
            ua=ua,
        )

    if inst.fees_paise > 0:
        await create_transaction(
            db,
            organization_id=organization_id,
            user_id=user_id,
            credit_card_id=plan.credit_card_id,
            tx_type=TransactionType.EMI_FEE,
            amount_paise=inst.fees_paise,
            occurred_at=occurred_at,
            merchant=f"EMI Fees - Month {inst.sequence_number}/{plan.tenure_months}",
            posting_status=PostingStatus.POSTED,
            ip=ip,
            ua=ua,
        )

    inst.status = EmiInstallmentStatus.PAID
    await db.flush()

    result_pending = await db.scalar(
        select(func.count(EmiInstallment.id)).where(
            EmiInstallment.plan_id == plan.id, EmiInstallment.status == EmiInstallmentStatus.PENDING
        )
    )
    if result_pending == 0:
        plan.status = EmiPlanStatus.COMPLETED

    await db.flush()
    return inst
