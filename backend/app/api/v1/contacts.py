"""Contact CRUD with outstanding balances."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession, OrgContext, client_meta
from app.core.exceptions import NotFoundError
from app.models.contact import Contact
from app.models.enums import ActivityAction
from app.schemas.common import PaginatedResponse
from app.schemas.domain import ContactCreate, ContactResponse, ContactUpdate
from app.services.ledger_service import contact_balance_paise, contacts_balances_map
from app.services.logging_service import log_activity

router = APIRouter(prefix="/contacts", tags=["contacts"])


def _to_response(contact: Contact, outstanding: int = 0) -> ContactResponse:
    data = ContactResponse.model_validate(contact)
    return data.model_copy(update={"outstanding_paise": outstanding})


@router.get("", response_model=PaginatedResponse[ContactResponse])
async def list_contacts(
    db: DbSession,
    org_ctx: OrgContext,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    include_archived: bool = False,
) -> PaginatedResponse[ContactResponse]:
    org, _ = org_ctx
    filters = [Contact.organization_id == org.id]
    if not include_archived:
        filters.append(Contact.archived_at.is_(None))

    total = await db.scalar(select(func.count()).select_from(Contact).where(*filters)) or 0
    result = await db.execute(
        select(Contact)
        .where(*filters)
        .order_by(Contact.name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    contacts = list(result.scalars().all())
    balances = await contacts_balances_map(db, org.id)
    items = [_to_response(c, balances.get(c.id, 0)) for c in contacts]
    return PaginatedResponse(items=items, total=int(total), page=page, page_size=page_size)


@router.post("", response_model=ContactResponse, status_code=201)
async def create_contact(
    body: ContactCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> ContactResponse:
    org, _ = org_ctx
    contact = Contact(
        id=uuid4(),
        organization_id=org.id,
        name=body.name,
        phone=body.phone,
        email=body.email,
        notes=body.notes,
        tags=body.tags,
    )
    db.add(contact)
    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.CONTACT_CREATE,
        summary=f"Created contact {contact.name}",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="contact",
        resource_id=str(contact.id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.commit()
    await db.refresh(contact)
    return _to_response(contact, 0)


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: UUID, db: DbSession, org_ctx: OrgContext) -> ContactResponse:
    org, _ = org_ctx
    contact = await _get(db, org.id, contact_id)
    outstanding = await contact_balance_paise(db, contact.id)
    return _to_response(contact, outstanding)


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    body: ContactUpdate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> ContactResponse:
    org, _ = org_ctx
    contact = await _get(db, org.id, contact_id)
    data = body.model_dump(exclude_unset=True)
    archived = data.pop("archived", None)
    for key, value in data.items():
        setattr(contact, key, value)
    if archived is True:
        contact.archived_at = datetime.now(UTC)
    elif archived is False:
        contact.archived_at = None
    ip, ua = client_meta(request)
    await log_activity(
        db,
        action=ActivityAction.CONTACT_UPDATE,
        summary=f"Updated contact {contact.name}",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="contact",
        resource_id=str(contact.id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.commit()
    await db.refresh(contact)
    outstanding = await contact_balance_paise(db, contact.id)
    return _to_response(contact, outstanding)


async def _get(db: DbSession, org_id: UUID, contact_id: UUID) -> Contact:
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.organization_id == org_id)
    )
    contact = result.scalar_one_or_none()
    if contact is None:
        raise NotFoundError("Contact not found")
    return contact
