"""Statement upload, parse, review, and import endpoints."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, Header, Query, Request, Response, UploadFile
from sqlalchemy import func, select

from app.api.deps import AppSettings, CurrentUser, DbSession, OrgContext, client_meta
from app.core.exceptions import AppError
from app.core.idempotency import IDEMPOTENCY_HEADER, execute_idempotent
from app.core.rate_limit import UPLOAD_LIMIT, enforce_rate_limit
from app.core.upload_limits import read_upload_limited
from app.models.enums import LineReviewStatus, StatementStatus
from app.models.statement import Statement, StatementLineCandidate
from app.schemas.common import PaginatedResponse
from app.schemas.domain import (
    StatementBulkReview,
    StatementDetailResponse,
    StatementImportResult,
    StatementLineResponse,
    StatementLineUpdate,
    StatementResponse,
)
from app.services import statement_service

router = APIRouter(prefix="/statements", tags=["statements"])


async def _line_counts(db: DbSession, statement_ids: list[UUID]) -> dict[UUID, dict[str, int]]:
    if not statement_ids:
        return {}
    result = await db.execute(
        select(
            StatementLineCandidate.statement_id,
            StatementLineCandidate.review_status,
            func.count(),
            func.count(StatementLineCandidate.committed_transaction_id),
        )
        .where(StatementLineCandidate.statement_id.in_(statement_ids))
        .group_by(
            StatementLineCandidate.statement_id,
            StatementLineCandidate.review_status,
        )
    )
    out: dict[UUID, dict[str, int]] = {
        sid: {"lines_count": 0, "pending_count": 0, "accepted_count": 0, "imported_count": 0}
        for sid in statement_ids
    }
    for sid, status, count, imported in result.all():
        bucket = out.setdefault(
            sid,
            {"lines_count": 0, "pending_count": 0, "accepted_count": 0, "imported_count": 0},
        )
        bucket["lines_count"] += int(count)
        if status == LineReviewStatus.PENDING:
            bucket["pending_count"] += int(count)
        if status in {LineReviewStatus.ACCEPTED, LineReviewStatus.EDITED}:
            bucket["accepted_count"] += int(count)
        bucket["imported_count"] += int(imported or 0)
    return out


def _to_response(row: Statement, counts: dict[str, int] | None = None) -> StatementResponse:
    data = StatementResponse.model_validate(row)
    if counts:
        return data.model_copy(update=counts)
    return data


@router.get("", response_model=PaginatedResponse[StatementResponse])
async def list_statements(
    db: DbSession,
    org_ctx: OrgContext,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    card_id: UUID | None = None,
    status: StatementStatus | None = None,
) -> PaginatedResponse[StatementResponse]:
    org, _ = org_ctx
    filters = [Statement.organization_id == org.id]
    if card_id:
        filters.append(Statement.credit_card_id == card_id)
    if status:
        filters.append(Statement.status == status)
    total = await db.scalar(select(func.count()).select_from(Statement).where(*filters)) or 0
    result = await db.execute(
        select(Statement)
        .where(*filters)
        .order_by(Statement.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = list(result.scalars().all())
    counts = await _line_counts(db, [r.id for r in rows])
    items = [_to_response(r, counts.get(r.id)) for r in rows]
    return PaginatedResponse(items=items, total=int(total), page=page, page_size=page_size)


@router.post("/upload", response_model=StatementDetailResponse, status_code=201)
async def upload_statement(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
    settings: AppSettings,
    file: UploadFile = File(...),
    credit_card_id: UUID = Form(...),
    period_start: date | None = Form(None),
    period_end: date | None = Form(None),
    statement_date: date | None = Form(None),
    due_date: date | None = Form(None),
    auto_parse: bool = Form(True),
) -> StatementDetailResponse:
    """Upload a statement PDF or FinBuddy sample .txt and optionally parse immediately."""
    await enforce_rate_limit(
        request, bucket="statement_upload", limit=UPLOAD_LIMIT, window_seconds=60.0
    )
    org, _ = org_ctx
    card = await statement_service.ensure_card(db, org.id, credit_card_id)
    data = await read_upload_limited(file, max_bytes=settings.statement_max_upload_bytes)
    filename = file.filename or "statement.bin"
    ip, ua = client_meta(request)

    statement = await statement_service.create_statement_from_upload(
        db,
        settings=settings,
        org_id=org.id,
        user_id=user.id,
        card=card,
        filename=filename,
        data=data,
        period_start=period_start,
        period_end=period_end,
        statement_date=statement_date,
        due_date=due_date,
        ip=ip,
        ua=ua,
    )

    if auto_parse:
        statement = await statement_service.run_parse(
            db,
            settings=settings,
            statement=statement,
            card=card,
            user_id=user.id,
            ip=ip,
            ua=ua,
        )

    await db.commit()
    await db.refresh(statement)
    return await _detail(db, org.id, statement)


@router.get("/{statement_id}", response_model=StatementDetailResponse)
async def get_statement(
    statement_id: UUID, db: DbSession, org_ctx: OrgContext
) -> StatementDetailResponse:
    org, _ = org_ctx
    statement = await statement_service.get_statement_or_404(db, org.id, statement_id)
    return await _detail(db, org.id, statement)


@router.post("/{statement_id}/parse", response_model=StatementDetailResponse)
async def parse_statement(
    statement_id: UUID,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
    settings: AppSettings,
) -> StatementDetailResponse:
    org, _ = org_ctx
    statement = await statement_service.get_statement_or_404(db, org.id, statement_id)
    if statement.status == StatementStatus.IMPORTED:
        raise AppError(
            "Cannot re-parse an imported statement",
            code="already_imported",
        )
    card = await statement_service.ensure_card(db, org.id, statement.credit_card_id)
    ip, ua = client_meta(request)
    statement = await statement_service.run_parse(
        db,
        settings=settings,
        statement=statement,
        card=card,
        user_id=user.id,
        ip=ip,
        ua=ua,
    )
    await db.commit()
    await db.refresh(statement)
    return await _detail(db, org.id, statement)


@router.get("/{statement_id}/lines", response_model=list[StatementLineResponse])
async def list_lines(
    statement_id: UUID, db: DbSession, org_ctx: OrgContext
) -> list[StatementLineResponse]:
    org, _ = org_ctx
    await statement_service.get_statement_or_404(db, org.id, statement_id)
    result = await db.execute(
        select(StatementLineCandidate)
        .where(
            StatementLineCandidate.statement_id == statement_id,
            StatementLineCandidate.organization_id == org.id,
        )
        .order_by(
            StatementLineCandidate.occurred_at.asc().nullslast(),
            StatementLineCandidate.created_at.asc(),
        )
    )
    return [StatementLineResponse.model_validate(row) for row in result.scalars().all()]


@router.patch("/{statement_id}/lines/{line_id}", response_model=StatementLineResponse)
async def update_line(
    statement_id: UUID,
    line_id: UUID,
    body: StatementLineUpdate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> StatementLineResponse:
    org, _ = org_ctx
    line = await statement_service.update_line(
        db,
        org_id=org.id,
        statement_id=statement_id,
        line_id=line_id,
        review_status=body.review_status,
        merchant=body.merchant,
        amount_paise=body.amount_paise,
        occurred_at=body.occurred_at,
        proposed_type=body.proposed_type,
        proposed_contact_id=body.proposed_contact_id,
        clear_contact=body.clear_contact,
    )
    ip, ua = client_meta(request)
    from app.models.enums import ActivityAction
    from app.services.logging_service import log_activity

    await log_activity(
        db,
        action=ActivityAction.STATEMENT_REVIEW,
        summary=f"Reviewed line {line_id} → {line.review_status.value}",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="statement_line",
        resource_id=str(line_id),
        ip_address=ip,
        user_agent=ua,
    )
    await db.commit()
    await db.refresh(line)
    return StatementLineResponse.model_validate(line)


@router.post("/{statement_id}/lines/bulk-review", response_model=dict)
async def bulk_review(
    statement_id: UUID,
    body: StatementBulkReview,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> dict[str, int]:
    org, _ = org_ctx
    if body.review_status not in {
        LineReviewStatus.ACCEPTED,
        LineReviewStatus.REJECTED,
        LineReviewStatus.PENDING,
    }:
        raise AppError("Bulk review supports accepted, rejected, or pending", code="invalid_status")
    count = await statement_service.bulk_set_review_status(
        db,
        org_id=org.id,
        statement_id=statement_id,
        review_status=body.review_status,
        only_pending=body.only_pending,
    )
    await db.commit()
    return {"updated": count}


@router.post("/{statement_id}/import", response_model=StatementImportResult)
async def import_statement(
    statement_id: UUID,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
    response: Response = Response(),
    idempotency_key: Annotated[str | None, Header(alias=IDEMPOTENCY_HEADER)] = None,
) -> StatementImportResult:
    org, _ = org_ctx
    ip, ua = client_meta(request)

    async def _action() -> tuple[int, StatementImportResult]:
        statement = await statement_service.get_statement_or_404(
            db, org.id, statement_id, for_update=True
        )
        result = await statement_service.import_statement(
            db,
            statement=statement,
            user_id=user.id,
            ip=ip,
            ua=ua,
        )
        await db.flush()
        await db.refresh(statement)
        counts = await _line_counts(db, [statement.id])
        res = StatementImportResult(
            created=result["created"],
            skipped=result["skipped"],
            status=statement.status,
            statement=_to_response(statement, counts.get(statement.id)),
        )
        return 200, res

    _, final_result = await execute_idempotent(
        db,
        organization_id=org.id,
        user_id=user.id,
        idempotency_key=idempotency_key,
        request_path=request.url.path,
        payload={"statement_id": str(statement_id)},
        action=_action,
        response=response,
        result_parser=StatementImportResult.model_validate,
    )
    return final_result


async def _detail(db: DbSession, org_id: UUID, statement: Statement) -> StatementDetailResponse:
    counts = await _line_counts(db, [statement.id])
    base = _to_response(statement, counts.get(statement.id))
    result = await db.execute(
        select(StatementLineCandidate)
        .where(
            StatementLineCandidate.statement_id == statement.id,
            StatementLineCandidate.organization_id == org_id,
        )
        .order_by(
            StatementLineCandidate.occurred_at.asc().nullslast(),
            StatementLineCandidate.created_at.asc(),
        )
    )
    lines = [StatementLineResponse.model_validate(row) for row in result.scalars().all()]
    return StatementDetailResponse(**base.model_dump(), lines=lines)
