"""EMI endpoints."""

from uuid import UUID

from fastapi import APIRouter, Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession, OrgContext
from app.models.emi import EmiPlan
from app.schemas.domain import EmiInstallmentResponse, EmiPlanCreate, EmiPlanResponse
from app.services.emi_service import create_emi_plan, pay_emi_installment

router = APIRouter(prefix="/emis", tags=["emis"])


@router.post("", response_model=EmiPlanResponse, status_code=201)
async def create_plan(
    body: EmiPlanCreate,
    db: DbSession,
    org_ctx: OrgContext,
) -> EmiPlanResponse:
    org, _ = org_ctx
    plan = await create_emi_plan(
        db,
        organization_id=org.id,
        credit_card_id=body.credit_card_id,
        reference_transaction_id=body.reference_transaction_id,
        principal_paise=body.principal_paise,
        interest_rate_bps=body.interest_rate_bps,
        tenure_months=body.tenure_months,
        start_date=body.start_date,
    )
    await db.commit()
    # Need to reload it with installments sorted
    await db.refresh(plan, ["installments"])
    plan.installments.sort(key=lambda x: x.sequence_number)
    return EmiPlanResponse.model_validate(plan)


@router.get("/card/{card_id}", response_model=list[EmiPlanResponse])
async def list_card_emi_plans(
    card_id: UUID,
    db: DbSession,
    org_ctx: OrgContext,
) -> list[EmiPlanResponse]:
    org, _ = org_ctx
    
    result = await db.execute(
        select(EmiPlan)
        .options(selectinload(EmiPlan.installments))
        .where(
            EmiPlan.organization_id == org.id,
            EmiPlan.credit_card_id == card_id,
        )
        .order_by(EmiPlan.created_at.desc())
    )
    
    plans = list(result.scalars().all())
    for plan in plans:
        plan.installments.sort(key=lambda x: x.sequence_number)
        
    return [EmiPlanResponse.model_validate(p) for p in plans]


@router.post("/installments/{installment_id}/pay", response_model=EmiInstallmentResponse)
async def pay_installment_api(
    installment_id: UUID,
    request: Request,
    db: DbSession,
    org_ctx: OrgContext,
) -> EmiInstallmentResponse:
    org, user = org_ctx
    inst = await pay_emi_installment(
        db,
        organization_id=org.id,
        user_id=user.id,
        installment_id=installment_id,
        ip=request.client.host if request.client else None,
        ua=request.headers.get("user-agent"),
    )
    return EmiInstallmentResponse.model_validate(inst)
