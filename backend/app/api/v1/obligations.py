"""Obligation endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request, Response
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, OrgAdminContext, OrgContext, client_meta
from app.core.exceptions import NotFoundError
from app.core.idempotency import IDEMPOTENCY_HEADER, execute_idempotent
from app.models.contact import Contact
from app.models.enums import ActivityAction, ObligationStatus, ObligationType
from app.models.obligation import Obligation
from app.schemas.common import PaginatedResponse
from app.schemas.domain import (
    ObligationCreate,
    ObligationPaymentCreate,
    ObligationPaymentResponse,
    ObligationResponse,
    ObligationUpdate,
)
from app.services import obligation_service
from app.services.logging_service import log_activity

router = APIRouter(prefix="/obligations", tags=["obligations"])


@router.get("", response_model=PaginatedResponse[ObligationResponse])
async def list_obligations(
    db: DbSession,
    org_ctx: OrgContext,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: ObligationStatus | None = None,
    type: ObligationType | None = None,
    contact_id: UUID | None = None,
) -> PaginatedResponse[ObligationResponse]:
    org, _ = org_ctx

    # Use the service to get obligations with calculated remaining balance
    # Currently this service method returns all records, so we apply python-side pagination.
    # In a very large table, we'd paginate inside the DB.
    # But since it's user-level data, python pagination of the list is acceptable for now.
    all_obligations = await obligation_service.list_obligations_with_balance(
        db,
        organization_id=org.id,
        status=status,
        type=type,
        contact_id=contact_id,
    )

    total = len(all_obligations)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = all_obligations[start:end]

    items = []
    for obl, remaining in page_items:
        res = ObligationResponse.model_validate(obl)
        res.remaining_paise = remaining
        items.append(res)

    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{obligation_id}", response_model=ObligationResponse)
async def get_obligation(
    obligation_id: UUID,
    db: DbSession,
    org_ctx: OrgContext,
) -> ObligationResponse:
    org, _ = org_ctx
    obl, remaining = await obligation_service.get_obligation_with_balance(
        db, organization_id=org.id, obligation_id=obligation_id
    )
    res = ObligationResponse.model_validate(obl)
    res.remaining_paise = remaining
    return res


@router.post("", response_model=ObligationResponse, status_code=201)
async def create_obligation(
    body: ObligationCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
    response: Response = Response(),
    idempotency_key: Annotated[str | None, Header(alias=IDEMPOTENCY_HEADER)] = None,
) -> ObligationResponse:
    org, _ = org_ctx

    async def _action() -> tuple[int, ObligationResponse]:
        if body.contact_id:
            contact = await db.execute(
                select(Contact.id).where(
                    Contact.id == body.contact_id, Contact.organization_id == org.id
                )
            )
            if contact.scalar_one_or_none() is None:
                raise NotFoundError("Contact not found")

        obl = await obligation_service.create_obligation(
            db,
            organization_id=org.id,
            user_id=user.id,
            type=body.type,
            amount_paise=body.amount_paise,
            currency=body.currency,
            contact_id=body.contact_id,
            counterparty_name=body.counterparty_name,
            due_date=body.due_date,
            notes=body.notes,
        )

        ip, ua = client_meta(request)
        await log_activity(
            db,
            action=ActivityAction.OBLIGATION_CREATE,
            summary=f"Created {body.type.value} obligation for {body.amount_paise} paise",
            actor_user_id=user.id,
            organization_id=org.id,
            resource_type="obligation",
            resource_id=str(obl.id),
            ip_address=ip,
            user_agent=ua,
        )
        await db.flush()
        await db.refresh(obl)

        res = ObligationResponse.model_validate(obl)
        res.remaining_paise = obl.amount_paise
        return 201, res

    _, result = await execute_idempotent(
        db,
        organization_id=org.id,
        user_id=user.id,
        idempotency_key=idempotency_key,
        request_path=request.url.path,
        payload=body,
        action=_action,
        response=response,
        result_parser=ObligationResponse.model_validate,
    )
    return result


@router.patch("/{obligation_id}", response_model=ObligationResponse)
async def update_obligation(
    obligation_id: UUID,
    body: ObligationUpdate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> ObligationResponse:
    org, _ = org_ctx

    obl = await obligation_service.update_obligation(
        db,
        organization_id=org.id,
        obligation_id=obligation_id,
        status=body.status,
        due_date=body.due_date,
        notes=body.notes,
    )

    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.OBLIGATION_UPDATE,
        summary=f"Updated obligation {obligation_id}",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="obligation",
        resource_id=str(obl.id),
        ip_address=ip,
        user_agent=ua,
    )

    await db.commit()

    # Refetch for the balanced response
    return await get_obligation(obligation_id=obligation_id, db=db, org_ctx=org_ctx)


@router.delete("/{obligation_id}", status_code=204)
async def delete_obligation(
    obligation_id: UUID,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgAdminContext,
) -> None:
    org, _ = org_ctx
    obl = await db.scalar(
        select(Obligation).where(
            Obligation.id == obligation_id, Obligation.organization_id == org.id
        )
    )
    if not obl:
        raise NotFoundError("Obligation not found")

    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.OBLIGATION_UPDATE,  # Or specific delete action if we had one
        summary=f"Deleted obligation {obligation_id}",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="obligation",
        resource_id=str(obligation_id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.delete(obl)
    await db.commit()


@router.post("/{obligation_id}/payments", response_model=ObligationPaymentResponse, status_code=201)
async def add_payment(
    obligation_id: UUID,
    body: ObligationPaymentCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
    response: Response = Response(),
    idempotency_key: Annotated[str | None, Header(alias=IDEMPOTENCY_HEADER)] = None,
) -> ObligationPaymentResponse:
    org, _ = org_ctx

    async def _action() -> tuple[int, ObligationPaymentResponse]:
        payment = await obligation_service.add_payment(
            db,
            organization_id=org.id,
            user_id=user.id,
            obligation_id=obligation_id,
            amount_paise=body.amount_paise,
            date=body.date,
            account_id=body.account_id,
            notes=body.notes,
        )

        ip, ua = client_meta(request)
        await log_activity(
            db,
            action=ActivityAction.OBLIGATION_PAYMENT,
            summary=f"Added payment of {body.amount_paise} paise to obligation {obligation_id}",
            actor_user_id=user.id,
            organization_id=org.id,
            resource_type="obligation",
            resource_id=str(obligation_id),
            ip_address=ip,
            user_agent=ua,
        )
        await db.flush()
        await db.refresh(payment)
        return 201, ObligationPaymentResponse.model_validate(payment)

    _, result = await execute_idempotent(
        db,
        organization_id=org.id,
        user_id=user.id,
        idempotency_key=idempotency_key,
        request_path=request.url.path,
        payload={"obligation_id": str(obligation_id), **body.model_dump(mode="json")},
        action=_action,
        response=response,
        result_parser=ObligationPaymentResponse.model_validate,
    )
    return result


@router.get("/{obligation_id}/payments", response_model=list[ObligationPaymentResponse])
async def list_payments(
    obligation_id: UUID,
    db: DbSession,
    org_ctx: OrgContext,
) -> list[ObligationPaymentResponse]:
    org, _ = org_ctx
    # verify existence
    await obligation_service.get_obligation_with_balance(
        db, organization_id=org.id, obligation_id=obligation_id
    )

    payments = await obligation_service.list_payments(
        db, organization_id=org.id, obligation_id=obligation_id
    )

    return [ObligationPaymentResponse.model_validate(p) for p in payments]
