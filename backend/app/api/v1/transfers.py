"""Transfer endpoints."""

from typing import Annotated

from fastapi import APIRouter, Header, Request, Response

from app.api.deps import CurrentUser, DbSession, OrgContext, client_meta
from app.core.idempotency import IDEMPOTENCY_HEADER, execute_idempotent
from app.schemas.domain import TransactionResponse, TransferCreate, TransferResponse
from app.services import transaction_service

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("", response_model=TransferResponse, status_code=201)
async def create_transfer(
    body: TransferCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
    response: Response = Response(),
    idempotency_key: Annotated[str | None, Header(alias=IDEMPOTENCY_HEADER)] = None,
) -> TransferResponse:
    org, _ = org_ctx
    ip, ua = client_meta(request)

    async def _action() -> tuple[int, TransferResponse]:
        tx_out, tx_in = await transaction_service.create_transfer(
            db,
            organization_id=org.id,
            user_id=user.id,
            from_account_id=body.from_account_id,
            to_account_id=body.to_account_id,
            amount_paise=body.amount_paise,
            occurred_at=body.occurred_at,
            notes=body.notes,
            tags=body.tags,
            ip=ip,
            ua=ua,
        )
        await db.flush()
        await db.refresh(tx_out)
        await db.refresh(tx_in)
        assert tx_out.transfer_group_id is not None
        transfer_resp = TransferResponse(
            transfer_group_id=tx_out.transfer_group_id,
            out_transaction=TransactionResponse.model_validate(tx_out),
            in_transaction=TransactionResponse.model_validate(tx_in),
        )
        return 201, transfer_resp

    _, result = await execute_idempotent(
        db,
        organization_id=org.id,
        user_id=user.id,
        idempotency_key=idempotency_key,
        request_path=request.url.path,
        payload=body,
        action=_action,
        response=response,
        result_parser=TransferResponse.model_validate,
    )
    return result
