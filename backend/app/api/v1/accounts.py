"""Accounts CRUD and balance corrections."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request, Response
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession, OrgAdminContext, OrgContext, client_meta
from app.core.idempotency import IDEMPOTENCY_HEADER, execute_idempotent
from app.models.account import Account
from app.models.enums import AccountKind, ActivityAction
from app.schemas.common import PaginatedResponse
from app.schemas.domain import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
    CorrectBalanceRequest,
    TransactionResponse,
)
from app.services import account_service
from app.services.ledger_service import account_balance_paise, accounts_balances_map
from app.services.logging_service import log_activity
from app.services.transaction_service import adjust_account_balance

router = APIRouter(prefix="/accounts", tags=["accounts"])


def _to_response(account: Account, balance: int) -> AccountResponse:
    data = AccountResponse.model_validate(account, from_attributes=True)
    return data.model_copy(update={"balance_paise": balance})


@router.get("", response_model=PaginatedResponse[AccountResponse])
async def list_accounts(
    db: DbSession,
    org_ctx: OrgContext,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    kind: AccountKind | None = None,
    include_archived: bool = False,
) -> PaginatedResponse[AccountResponse]:
    org, _ = org_ctx
    filters = [Account.organization_id == org.id]
    if kind is not None:
        filters.append(Account.kind == kind)
    if not include_archived:
        filters.append(Account.archived_at.is_(None))
    total = await db.scalar(select(func.count()).select_from(Account).where(*filters)) or 0
    result = await db.execute(
        select(Account)
        .where(*filters)
        .order_by(Account.kind.asc(), Account.name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    accounts = list(result.scalars().all())
    balances = await accounts_balances_map(db, org.id)
    return PaginatedResponse(
        items=[_to_response(account, balances.get(account.id, 0)) for account in accounts],
        total=int(total),
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=AccountResponse, status_code=201)
async def create_account(
    body: AccountCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgAdminContext,
    response: Response = Response(),
    idempotency_key: Annotated[str | None, Header(alias=IDEMPOTENCY_HEADER)] = None,
) -> AccountResponse:
    org, _ = org_ctx

    async def _action() -> tuple[int, AccountResponse]:
        account = await account_service.create_account(
            db,
            organization_id=org.id,
            kind=body.kind,
            name=body.name,
            institution=body.institution,
            currency=body.currency,
        )
        if body.opening_balance_paise:
            await adjust_account_balance(
                db,
                organization_id=org.id,
                user_id=user.id,
                account=account,
                delta_paise=body.opening_balance_paise,
                reason="Opening balance",
                merchant="Opening balance",
            )
        ip, ua = client_meta(request)
        await log_activity(
            db,
            action=ActivityAction.OTHER,
            summary=f"Created account {account.name}",
            actor_user_id=user.id,
            organization_id=org.id,
            resource_type="account",
            resource_id=str(account.id),
            ip_address=ip,
            user_agent=ua,
        )
        await db.flush()
        await db.refresh(account)
        bal = await account_balance_paise(db, account.id)
        return 201, _to_response(account, bal)

    _, final_result = await execute_idempotent(
        db,
        organization_id=org.id,
        user_id=user.id,
        idempotency_key=idempotency_key,
        request_path=request.url.path,
        payload=body,
        action=_action,
        response=response,
        result_parser=AccountResponse.model_validate,
    )
    return final_result


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: UUID, db: DbSession, org_ctx: OrgContext) -> AccountResponse:
    org, _ = org_ctx
    account = await account_service.get_account(db, organization_id=org.id, account_id=account_id)
    return _to_response(account, await account_balance_paise(db, account.id))


@router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: UUID,
    body: AccountUpdate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgAdminContext,
) -> AccountResponse:
    org, _ = org_ctx
    account = await account_service.update_account(
        db,
        organization_id=org.id,
        account_id=account_id,
        **body.model_dump(exclude_unset=True),
    )
    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.OTHER,
        summary=f"Updated account {account.name}",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="account",
        resource_id=str(account.id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.commit()
    await db.refresh(account)
    return _to_response(account, await account_balance_paise(db, account.id))


@router.post("/{account_id}/archive", response_model=AccountResponse)
async def archive_account(
    account_id: UUID,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgAdminContext,
) -> AccountResponse:
    org, _ = org_ctx
    account = await account_service.archive_account(
        db,
        organization_id=org.id,
        account_id=account_id,
        archived_at=datetime.now(UTC),
    )
    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.OTHER,
        summary=f"Archived account {account.name}",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="account",
        resource_id=str(account.id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.commit()
    await db.refresh(account)
    return _to_response(account, await account_balance_paise(db, account.id))


@router.post("/{account_id}/correct-balance", response_model=TransactionResponse, status_code=201)
async def correct_balance(
    account_id: UUID,
    body: CorrectBalanceRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgAdminContext,
    response: Response = Response(),
    idempotency_key: Annotated[str | None, Header(alias=IDEMPOTENCY_HEADER)] = None,
) -> TransactionResponse:
    org, _ = org_ctx
    ip, ua = client_meta(request)

    async def _action() -> tuple[int, TransactionResponse]:
        transaction = await account_service.correct_balance(
            db,
            organization_id=org.id,
            user_id=user.id,
            account_id=account_id,
            target_balance_paise=body.target_balance_paise,
            reason=body.reason,
            occurred_at=body.occurred_at,
            ip=ip,
            ua=ua,
        )
        await db.flush()
        await db.refresh(transaction)
        return 201, TransactionResponse.model_validate(transaction)

    _, final_result = await execute_idempotent(
        db,
        organization_id=org.id,
        user_id=user.id,
        idempotency_key=idempotency_key,
        request_path=request.url.path,
        payload=body,
        action=_action,
        response=response,
        result_parser=TransactionResponse.model_validate,
    )
    return final_result
