"""Transfer endpoints."""

from fastapi import APIRouter, Request

from app.api.deps import CurrentUser, DbSession, OrgContext, client_meta
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
) -> TransferResponse:
    org, _ = org_ctx
    ip, ua = client_meta(request)
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
    await db.commit()
    await db.refresh(tx_out)
    await db.refresh(tx_in)
    assert tx_out.transfer_group_id is not None
    return TransferResponse(
        transfer_group_id=tx_out.transfer_group_id,
        out_transaction=TransactionResponse.model_validate(tx_out),
        in_transaction=TransactionResponse.model_validate(tx_in),
    )
