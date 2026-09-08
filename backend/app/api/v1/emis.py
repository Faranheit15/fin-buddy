"""EMI endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession, OrgAdminContext, OrgContext
from app.core.idempotency import IDEMPOTENCY_HEADER, execute_idempotent
from app.models.emi import EmiPlan
from app.schemas.domain import EmiInstallmentResponse, EmiPlanCreate, EmiPlanResponse
from app.services.emi_service import create_emi_plan, pay_emi_installment

router = APIRouter(prefix="/emis", tags=["emis"])


@router.post("", response_model=EmiPlanResponse, status_code=201)
async def create_plan(
    body: EmiPlanCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgAdminContext,
    response: Response = Response(),
    idempotency_key: Annotated[str | None, Header(alias=IDEMPOTENCY_HEADER)] = None,
) -> EmiPlanResponse:
    org, _ = org_ctx

    async def _action() -> tuple[int, EmiPlanResponse]:
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
        await db.flush()
        # Need to reload it with installments sorted
        await db.refresh(plan, ["installments"])
        plan.installments.sort(key=lambda x: x.sequence_number)
        return 201, EmiPlanResponse.model_validate(plan)

    _, result = await execute_idempotent(
        db,
        organization_id=org.id,
        user_id=user.id,
        idempotency_key=idempotency_key,
        request_path=request.url.path,
        payload=body,
        action=_action,
        response=response,
        result_parser=EmiPlanResponse.model_validate,
    )
    return result


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
    user: CurrentUser,
    org_ctx: OrgContext,
    response: Response = Response(),
    idempotency_key: Annotated[str | None, Header(alias=IDEMPOTENCY_HEADER)] = None,
) -> EmiInstallmentResponse:
    org, _ = org_ctx

    async def _action() -> tuple[int, EmiInstallmentResponse]:
        inst = await pay_emi_installment(
            db,
            organization_id=org.id,
            user_id=user.id,
            installment_id=installment_id,
            ip=request.client.host if request.client else None,
            ua=request.headers.get("user-agent"),
        )
        await db.flush()
        await db.refresh(inst)
        return 200, EmiInstallmentResponse.model_validate(inst)

    _, result = await execute_idempotent(
        db,
        organization_id=org.id,
        user_id=user.id,
        idempotency_key=idempotency_key,
        request_path=request.url.path,
        payload={"installment_id": str(installment_id)},
        action=_action,
        response=response,
        result_parser=EmiInstallmentResponse.model_validate,
    )
    return result
