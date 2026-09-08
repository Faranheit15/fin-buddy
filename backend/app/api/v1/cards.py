"""Credit card CRUD."""

from datetime import UTC, datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession, OrgAdminContext, OrgContext, client_meta
from app.core.exceptions import NotFoundError
from app.domain.billing import (
    DueRuleType as DomainDueRuleType,
)
from app.domain.billing import (
    next_due_date_for_card,
    next_statement_date,
)
from app.models.account import Account
from app.models.credit_card import CreditCard
from app.models.enums import AccountKind, ActivityAction, CardStatus, PostingStatus, TransactionType
from app.models.transaction import Transaction
from app.schemas.common import PaginatedResponse
from app.schemas.domain import CreditCardCreate, CreditCardResponse, CreditCardUpdate
from app.services.emi_service import card_emi_blocked_paise, cards_emi_blocked_map
from app.services.ledger_service import card_outstanding_paise, cards_outstanding_map
from app.services.logging_service import log_activity
from app.services.org_validators import validate_contact_in_org

router = APIRouter(prefix="/cards", tags=["cards"])
IST = ZoneInfo("Asia/Kolkata")


def _cycle_dates(card: CreditCard) -> tuple[object, object]:
    today = datetime.now(IST).date()
    rule = DomainDueRuleType(card.due_rule_type.value)
    stmt = next_statement_date(today, card.statement_day)
    due = next_due_date_for_card(
        today,
        statement_day=card.statement_day,
        due_rule_type=rule,
        due_rule_value=card.due_rule_value,
    )
    return stmt, due


def _to_response(card: CreditCard, outstanding: int, emi_blocked: int = 0) -> CreditCardResponse:
    spend_outstanding = outstanding - emi_blocked
    available = max(card.credit_limit_paise - outstanding, 0)
    util = (
        round((outstanding / card.credit_limit_paise) * 100, 1)
        if card.credit_limit_paise > 0
        else 0.0
    )
    next_stmt, next_due = _cycle_dates(card)
    return CreditCardResponse(
        id=card.id,
        organization_id=card.organization_id,
        nickname=card.nickname,
        issuer=card.issuer,
        network=card.network,
        last_four=card.last_four,
        credit_limit_paise=card.credit_limit_paise,
        currency=card.currency,
        statement_day=card.statement_day,
        due_rule_type=card.due_rule_type,
        due_rule_value=card.due_rule_value,
        status=card.status,
        held_by_contact_id=card.held_by_contact_id,
        notes=card.notes,
        outstanding_paise=outstanding,
        spend_outstanding_paise=spend_outstanding,
        emi_principal_blocked_paise=emi_blocked,
        available_credit_paise=available,
        utilization_percent=util,
        next_statement_date=next_stmt,  # type: ignore[arg-type]
        next_due_date=next_due,  # type: ignore[arg-type]
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


@router.get("", response_model=PaginatedResponse[CreditCardResponse])
async def list_cards(
    db: DbSession,
    org_ctx: OrgContext,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    include_closed: bool = False,
) -> PaginatedResponse[CreditCardResponse]:
    org, _ = org_ctx
    filters = [CreditCard.organization_id == org.id]
    if not include_closed:
        filters.append(CreditCard.status == CardStatus.ACTIVE)

    total = await db.scalar(select(func.count()).select_from(CreditCard).where(*filters)) or 0
    result = await db.execute(
        select(CreditCard)
        .where(*filters)
        .order_by(CreditCard.nickname.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    cards = list(result.scalars().all())
    outstanding = await cards_outstanding_map(db, org.id)
    emi_blocked_map = await cards_emi_blocked_map(db, org.id)
    items = [_to_response(c, outstanding.get(c.id, 0), emi_blocked_map.get(c.id, 0)) for c in cards]
    return PaginatedResponse(items=items, total=int(total), page=page, page_size=page_size)


@router.post("", response_model=CreditCardResponse, status_code=201)
async def create_card(
    body: CreditCardCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgAdminContext,
) -> CreditCardResponse:
    org, _ = org_ctx
    if body.held_by_contact_id is not None:
        await validate_contact_in_org(db, org.id, body.held_by_contact_id)
    card = CreditCard(
        id=uuid4(),
        organization_id=org.id,
        nickname=body.nickname,
        issuer=body.issuer,
        network=body.network,
        last_four=body.last_four,
        credit_limit_paise=body.credit_limit_paise,
        currency=body.currency,
        statement_day=body.statement_day,
        due_rule_type=body.due_rule_type,
        due_rule_value=body.due_rule_value,
        held_by_contact_id=body.held_by_contact_id,
        notes=body.notes,
    )
    db.add(card)
    await db.flush()

    account = Account(
        id=uuid4(),
        organization_id=org.id,
        kind=AccountKind.CREDIT_CARD,
        name=card.nickname,
        institution=card.issuer,
        currency=card.currency,
        credit_card_id=card.id,
    )
    db.add(account)
    await db.flush()

    if body.opening_balance_paise:
        db.add(
            Transaction(
                id=uuid4(),
                organization_id=org.id,
                account_id=account.id,
                credit_card_id=card.id,
                type=TransactionType.OPENING_BALANCE,
                posting_status=PostingStatus.POSTED,
                amount_paise=body.opening_balance_paise,
                currency=body.currency,
                occurred_at=datetime.now(UTC),
                merchant="Opening balance",
                created_by=user.id,
            )
        )

    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.CARD_CREATE,
        summary=f"Created card {card.nickname}",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="credit_card",
        resource_id=str(card.id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.commit()
    await db.refresh(card)
    outstanding = await card_outstanding_paise(db, card.id)
    emi_blocked = await card_emi_blocked_paise(db, card.id)
    return _to_response(card, outstanding, emi_blocked)


@router.get("/{card_id}", response_model=CreditCardResponse)
async def get_card(card_id: UUID, db: DbSession, org_ctx: OrgContext) -> CreditCardResponse:
    org, _ = org_ctx
    card = await _get(db, org.id, card_id)
    outstanding = await card_outstanding_paise(db, card.id)
    emi_blocked = await card_emi_blocked_paise(db, card.id)
    return _to_response(card, outstanding, emi_blocked)


@router.patch("/{card_id}", response_model=CreditCardResponse)
async def update_card(
    card_id: UUID,
    body: CreditCardUpdate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgAdminContext,
) -> CreditCardResponse:
    org, _ = org_ctx
    card = await _get(db, org.id, card_id)
    if body.held_by_contact_id is not None:
        await validate_contact_in_org(db, org.id, body.held_by_contact_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(card, key, value)
    ip, ua = client_meta(request)
    action = (
        ActivityAction.CARD_ARCHIVE
        if body.status == CardStatus.CLOSED
        else ActivityAction.CARD_UPDATE
    )
    await log_activity(
        db,
        action=action,
        summary=f"Updated card {card.nickname}",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="credit_card",
        resource_id=str(card.id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.commit()
    await db.refresh(card)
    outstanding = await card_outstanding_paise(db, card.id)
    emi_blocked = await card_emi_blocked_paise(db, card.id)
    return _to_response(card, outstanding, emi_blocked)


async def _get(db: DbSession, org_id: UUID, card_id: UUID) -> CreditCard:
    result = await db.execute(
        select(CreditCard).where(CreditCard.id == card_id, CreditCard.organization_id == org_id)
    )
    card = result.scalar_one_or_none()
    if card is None:
        raise NotFoundError("Card not found")
    return card
