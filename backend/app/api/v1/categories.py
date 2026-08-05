"""Category endpoints."""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, OrgContext
from app.schemas.domain import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> list[CategoryResponse]:
    org, _ = org_ctx
    categories = await category_service.get_categories(db, org.id)
    return [CategoryResponse.model_validate(c) for c in categories]


@router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(
    body: CategoryCreate,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> CategoryResponse:
    org, _ = org_ctx
    cat = await category_service.create_category(
        db,
        org_id=org.id,
        name=body.name,
        kind=body.kind,
        color=body.color,
        icon=body.icon,
    )
    await db.commit()
    await db.refresh(cat)
    return CategoryResponse.model_validate(cat)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    body: CategoryUpdate,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> CategoryResponse:
    org, _ = org_ctx
    cat = await category_service.update_category(
        db,
        org_id=org.id,
        category_id=category_id,
        patch=body.model_dump(exclude_unset=True),
    )
    await db.commit()
    await db.refresh(cat)
    return CategoryResponse.model_validate(cat)


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: UUID,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> None:
    org, _ = org_ctx
    await category_service.delete_category(
        db,
        org_id=org.id,
        category_id=category_id,
    )
    await db.commit()
