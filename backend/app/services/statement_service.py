"""Statement upload → parse → review → import pipeline."""

from __future__ import annotations

import asyncio
import io
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta
from functools import partial
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AppError, NotFoundError
from app.core.upload_limits import (
    statement_file_spec,
    validate_statement_bytes,
)
from app.models.credit_card import CreditCard
from app.models.enums import (
    ActivityAction,
    LineReviewStatus,
    PostingStatus,
    StatementStatus,
    TransactionType,
)
from app.models.notification import InAppNotification
from app.models.statement import Statement, StatementLineCandidate
from app.models.transaction import Transaction
from app.services import storage
from app.services.account_service import resolve_account_id_for_card
from app.services.logging_service import log_activity
from app.services.org_validators import validate_contact_in_org

_PARSER_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="statement-parser")


def extract_text_from_bytes(
    data: bytes,
    filename: str,
    *,
    max_pdf_pages: int = 50,
    max_text_chars: int = 1_000_000,
) -> str:
    """Extract text from PDF or plain text/CSV uploads."""
    name = (filename or "").lower()
    if name.endswith((".txt", ".csv", ".tsv")) or _looks_like_text(data):
        text = data.decode("utf-8", errors="replace")
        if len(text) > max_text_chars:
            raise AppError(
                "The statement exceeds the parser text limit", code="parser_resource_limit"
            )
        return text

    # PDF via pypdf
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise AppError(
            "PDF support not installed (pypdf missing)",
            code="pdf_dependency_missing",
            status_code=500,
        ) from exc

    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        if len(reader.pages) > max_pdf_pages:
            raise AppError(
                "The statement exceeds the parser page limit", code="parser_resource_limit"
            )
        chunks: list[str] = []
        for page in reader.pages:
            chunks.append(page.extract_text() or "")
            if sum(len(chunk) for chunk in chunks) > max_text_chars:
                raise AppError(
                    "The statement exceeds the parser text limit", code="parser_resource_limit"
                )
        text = "\n".join(chunks).strip()
        if not text:
            raise AppError(
                "Could not extract text from PDF (empty or image-only). "
                "Try a text-based statement or FinBuddy sample .txt format.",
                code="pdf_empty_text",
            )
        return text
    except AppError:
        raise
    except Exception as exc:
        raise AppError(
            "The PDF is malformed, unreadable, or uses unsupported content",
            code="pdf_read_failed",
        ) from exc


def _looks_like_text(data: bytes) -> bool:
    if data.startswith(b"%PDF"):
        return False
    sample = data[:2048]
    if not sample:
        return True
    # If mostly printable / whitespace, treat as text
    printable = sum(1 for b in sample if 32 <= b < 127 or b in (9, 10, 13))
    return printable / len(sample) > 0.85


async def get_statement_or_404(
    db: AsyncSession, org_id: UUID, statement_id: UUID, for_update: bool = False
) -> Statement:
    stmt = select(Statement).where(
        Statement.id == statement_id, Statement.organization_id == org_id
    )
    if for_update:
        stmt = stmt.with_for_update()
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        raise NotFoundError("Statement not found")
    return row


async def ensure_card(db: AsyncSession, org_id: UUID, card_id: UUID) -> CreditCard:
    result = await db.execute(
        select(CreditCard).where(CreditCard.id == card_id, CreditCard.organization_id == org_id)
    )
    card = result.scalar_one_or_none()
    if card is None:
        raise NotFoundError("Credit card not found")
    return card


async def create_statement_from_upload(
    db: AsyncSession,
    *,
    settings: Settings,
    org_id: UUID,
    user_id: UUID,
    card: CreditCard,
    filename: str,
    content_type: str,
    data: bytes,
    period_start: date | None = None,
    period_end: date | None = None,
    statement_date: date | None = None,
    due_date: date | None = None,
    ip: str | None = None,
    ua: str | None = None,
) -> Statement:
    spec = validate_statement_bytes(
        data,
        filename,
        content_type,
        max_bytes=settings.statement_max_upload_bytes,
        max_decompressed_bytes=settings.statement_parser_max_decompressed_bytes,
    )

    statement_id = uuid4()
    relative = storage.statement_relative_path(org_id, statement_id, spec.extension)
    await storage.save_bytes(relative, data, settings)

    statement = Statement(
        id=statement_id,
        organization_id=org_id,
        credit_card_id=card.id,
        period_start=period_start,
        period_end=period_end,
        statement_date=statement_date,
        due_date=due_date,
        pdf_storage_path=relative,
        status=StatementStatus.UPLOADED,
        created_by=user_id,
    )
    db.add(statement)
    await log_activity(
        db,
        action=ActivityAction.STATEMENT_UPLOAD,
        summary=f"Uploaded statement for card {card.nickname} ({filename})",
        actor_user_id=user_id,
        organization_id=org_id,
        resource_type="statement",
        resource_id=str(statement.id),
        ip_address=ip,
        user_agent=ua,
        metadata={"filename": filename, "bytes": len(data)},
    )
    await db.flush()
    return statement


async def cleanup_abandoned_uploads(
    db: AsyncSession,
    *,
    settings: Settings,
    org_id: UUID,
    limit: int = 5,
) -> int:
    """Bound cleanup to stale prepare rows; reviewed/imported statements are never touched."""
    cutoff = datetime.now(UTC) - timedelta(seconds=settings.statement_abandon_after_seconds)
    result = await db.execute(
        select(Statement)
        .where(
            Statement.organization_id == org_id,
            Statement.status.in_([StatementStatus.UPLOADED, StatementStatus.FAILED]),
            Statement.pdf_storage_path.is_not(None),
            Statement.created_at < cutoff,
        )
        .order_by(Statement.created_at.asc())
        .limit(limit)
        .with_for_update()
    )
    rows = list(result.scalars().all())
    for row in rows:
        await storage.delete_file(row.pdf_storage_path, settings)
        await db.delete(row)
    if rows:
        await db.flush()
    return len(rows)


async def prepare_statement_upload(
    db: AsyncSession,
    *,
    settings: Settings,
    org_id: UUID,
    user_id: UUID,
    card: CreditCard,
    filename: str,
    content_type: str,
    size_bytes: int,
    period_start: date | None = None,
    period_end: date | None = None,
    statement_date: date | None = None,
    due_date: date | None = None,
) -> tuple[Statement, str]:
    """Create the durable metadata row and return its server-owned Storage path."""
    spec = statement_file_spec(
        filename,
        content_type,
        size_bytes,
        max_bytes=settings.statement_max_upload_bytes,
    )
    await cleanup_abandoned_uploads(db, settings=settings, org_id=org_id)
    statement_id = uuid4()
    statement = Statement(
        id=statement_id,
        organization_id=org_id,
        credit_card_id=card.id,
        period_start=period_start,
        period_end=period_end,
        statement_date=statement_date,
        due_date=due_date,
        pdf_storage_path=storage.statement_relative_path(
            org_id, statement_id, spec.extension, user_id
        ),
        status=StatementStatus.UPLOADED,
        created_by=user_id,
    )
    db.add(statement)
    await db.flush()
    return statement, statement.pdf_storage_path or ""


async def log_statement_upload(
    db: AsyncSession,
    *,
    statement: Statement,
    user_id: UUID,
    filename: str,
    size_bytes: int,
    ip: str | None = None,
    ua: str | None = None,
) -> None:
    await log_activity(
        db,
        action=ActivityAction.STATEMENT_UPLOAD,
        summary=f"Uploaded statement ({filename})",
        actor_user_id=user_id,
        organization_id=statement.organization_id,
        resource_type="statement",
        resource_id=str(statement.id),
        ip_address=ip,
        user_agent=ua,
        metadata={"filename": filename, "bytes": size_bytes},
    )


async def reject_upload(
    db: AsyncSession,
    *,
    settings: Settings,
    statement: Statement,
    message: str,
) -> None:
    """Delete untrusted content and leave an auditable failed metadata row."""
    path = statement.pdf_storage_path
    deleted = True
    try:
        await storage.delete_file(path, settings)
    except Exception:
        # Keep the API error truthful while the bounded stale-upload cleanup gets another chance.
        deleted = False
    if deleted:
        statement.pdf_storage_path = None
    statement.status = StatementStatus.FAILED
    statement.parse_error = message
    await db.flush()


async def finalize_statement_upload(
    db: AsyncSession,
    *,
    settings: Settings,
    org_id: UUID,
    user_id: UUID,
    statement_id: UUID,
    filename: str,
    content_type: str,
    size_bytes: int,
) -> Statement:
    """Verify the Storage object before it can enter parsing/review."""
    statement = await get_statement_or_404(db, org_id, statement_id, for_update=True)
    if statement.created_by != user_id:
        raise NotFoundError("Statement not found")
    if statement.status != StatementStatus.UPLOADED:
        return statement
    if not statement.pdf_storage_path:
        raise AppError(
            "Statement upload is no longer available", code="upload_not_ready", status_code=409
        )
    created_at = statement.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    if datetime.now(UTC) - created_at > timedelta(seconds=settings.statement_upload_ttl_seconds):
        await reject_upload(
            db,
            settings=settings,
            statement=statement,
            message="The upload session expired. Please upload the file again.",
        )
        raise AppError(
            "The upload session expired. Please upload the file again.",
            code="upload_expired",
            status_code=409,
        )

    try:
        expected = statement.pdf_storage_path.rsplit(".", 1)[-1]
        requested = statement_file_spec(
            filename,
            content_type,
            size_bytes,
            max_bytes=settings.statement_max_upload_bytes,
        )
        if requested.extension != expected:
            raise AppError(
                "The uploaded file metadata does not match its upload session",
                code="upload_metadata_mismatch",
            )
        metadata = await storage.object_metadata(statement.pdf_storage_path, settings)
        if metadata.size_bytes != size_bytes:
            raise AppError(
                "The uploaded file size does not match its upload session",
                code="upload_metadata_mismatch",
            )
        actual_content_type = (
            (metadata.content_type or content_type).split(";", 1)[0].strip().lower()
        )
        data = await storage.read_bytes(
            statement.pdf_storage_path,
            settings,
            max_bytes=settings.statement_max_upload_bytes,
        )
        validate_statement_bytes(
            data,
            filename,
            actual_content_type,
            max_bytes=settings.statement_max_upload_bytes,
            max_decompressed_bytes=settings.statement_parser_max_decompressed_bytes,
        )
    except FileNotFoundError as exc:
        await reject_upload(
            db,
            settings=settings,
            statement=statement,
            message="The upload expired before it could be finalized. Please upload the file again.",
        )
        raise AppError(
            "The upload expired before it could be finalized. Please upload the file again.",
            code="upload_not_ready",
            status_code=409,
        ) from exc
    except AppError as exc:
        await reject_upload(
            db,
            settings=settings,
            statement=statement,
            message=exc.message,
        )
        raise
    return statement


async def run_parse(
    db: AsyncSession,
    *,
    settings: Settings,
    statement: Statement,
    card: CreditCard,
    user_id: UUID,
    ip: str | None = None,
    ua: str | None = None,
) -> Statement:
    """Extract text, run parser, replace pending candidates."""
    statement.status = StatementStatus.PARSING
    statement.parse_error = None
    await db.flush()

    try:
        if not statement.pdf_storage_path:
            raise AppError("No file stored for statement", code="missing_file")
        metadata = await storage.object_metadata(statement.pdf_storage_path, settings)
        data = await storage.read_bytes(
            statement.pdf_storage_path,
            settings,
            max_bytes=settings.statement_max_upload_bytes,
        )
        filename = statement.pdf_storage_path.rsplit("/", 1)[-1]
        content_type = (metadata.content_type or "").split(";", 1)[0].strip().lower()
        validate_statement_bytes(
            data,
            filename,
            content_type,
            max_bytes=settings.statement_max_upload_bytes,
            max_decompressed_bytes=settings.statement_parser_max_decompressed_bytes,
        )

        from app.services.parsers import parse_statement_bytes

        parse_call = partial(
            parse_statement_bytes,
            data,
            filename,
            issuer=card.issuer,
            max_rows=settings.statement_parser_max_rows,
            max_columns=settings.statement_parser_max_columns,
            max_sheets=settings.statement_parser_max_sheets,
            max_pdf_pages=settings.statement_parser_max_pdf_pages,
            max_decompressed_bytes=settings.statement_parser_max_decompressed_bytes,
            max_lines=settings.statement_parser_max_lines,
            max_text_chars=settings.statement_parser_max_text_chars,
        )
        result = await asyncio.wait_for(
            asyncio.get_running_loop().run_in_executor(_PARSER_EXECUTOR, parse_call),
            timeout=settings.statement_parse_timeout_seconds,
        )

        # Fill metadata if missing
        if statement.period_start is None and result.period_start:
            statement.period_start = result.period_start
        if statement.period_end is None and result.period_end:
            statement.period_end = result.period_end
        if statement.statement_date is None and result.statement_date:
            statement.statement_date = result.statement_date
        if statement.due_date is None and result.due_date:
            statement.due_date = result.due_date

        # Drop previous uncommitted candidates (re-parse)
        await db.execute(
            delete(StatementLineCandidate).where(
                StatementLineCandidate.statement_id == statement.id,
                StatementLineCandidate.committed_transaction_id.is_(None),
            )
        )

        for line in result.lines:
            db.add(
                StatementLineCandidate(
                    id=uuid4(),
                    statement_id=statement.id,
                    organization_id=statement.organization_id,
                    raw_payload=line.raw,
                    occurred_at=line.occurred_at,
                    merchant=line.merchant,
                    amount_paise=line.amount_paise,
                    proposed_type=line.proposed_type,
                    proposed_contact_id=None,
                    review_status=LineReviewStatus.PENDING,
                )
            )

        if not result.lines:
            statement.status = StatementStatus.FAILED
            statement.parse_error = (
                f"Parser '{result.parser_name}' found no transaction lines. "
                "Try FinBuddy sample format or edit PDF text extraction."
            )
        else:
            statement.status = StatementStatus.NEEDS_REVIEW
            statement.parse_error = None
            # In-app notification
            db.add(
                InAppNotification(
                    id=uuid4(),
                    organization_id=statement.organization_id,
                    user_id=user_id,
                    type="statement_ready",
                    title="Statement ready for review",
                    body=f"{len(result.lines)} proposed lines from {card.nickname}",
                    href=f"/app/statements/{statement.id}",
                )
            )

        await log_activity(
            db,
            action=ActivityAction.STATEMENT_REVIEW,
            summary=(
                f"Parsed statement with {result.parser_name}: "
                f"{len(result.lines)} lines, status={statement.status.value}"
            ),
            actor_user_id=user_id,
            organization_id=statement.organization_id,
            resource_type="statement",
            resource_id=str(statement.id),
            ip_address=ip,
            user_agent=ua,
            metadata={"parser": result.parser_name, "line_count": len(result.lines)},
        )
    except TimeoutError:
        await reject_upload(
            db,
            settings=settings,
            statement=statement,
            message="The statement took too long to parse. Try a smaller, simpler file.",
        )
        statement.parse_error = "The statement took too long to parse. Try a smaller, simpler file."
    except FileNotFoundError:
        await reject_upload(
            db,
            settings=settings,
            statement=statement,
            message="The statement file is no longer available. Upload it again.",
        )
    except AppError as exc:
        statement.status = StatementStatus.FAILED
        statement.parse_error = exc.message
        if exc.code in {
            "invalid_file_content",
            "invalid_file_type",
            "unsupported_file_type",
            "parser_resource_limit",
            "pdf_read_failed",
            "pdf_empty_text",
            "tabular_read_failed",
            "missing_columns",
        }:
            await reject_upload(db, settings=settings, statement=statement, message=exc.message)
    except Exception:  # pragma: no cover
        statement.status = StatementStatus.FAILED
        statement.parse_error = "Statement parsing failed. Try a smaller, supported file."

    await db.flush()
    return statement


async def update_line(
    db: AsyncSession,
    *,
    org_id: UUID,
    statement_id: UUID,
    line_id: UUID,
    review_status: LineReviewStatus | None = None,
    merchant: str | None = None,
    amount_paise: int | None = None,
    occurred_at: datetime | None = None,
    proposed_type: TransactionType | None = None,
    proposed_contact_id: UUID | None = None,
    clear_contact: bool = False,
) -> StatementLineCandidate:
    statement = await get_statement_or_404(db, org_id, statement_id)
    if statement.status == StatementStatus.IMPORTED:
        raise AppError(
            "Statement is already imported; line edits are locked",
            code="statement_already_imported",
        )

    result = await db.execute(
        select(StatementLineCandidate).where(
            StatementLineCandidate.id == line_id,
            StatementLineCandidate.statement_id == statement_id,
            StatementLineCandidate.organization_id == org_id,
        )
    )
    line = result.scalar_one_or_none()
    if line is None:
        raise NotFoundError("Statement line not found")
    if line.committed_transaction_id is not None:
        raise AppError("Line already imported", code="line_already_imported")

    if merchant is not None:
        line.merchant = merchant[:255]
    if amount_paise is not None:
        if amount_paise <= 0:
            raise AppError("amount_paise must be > 0", code="invalid_amount")
        line.amount_paise = amount_paise
    if occurred_at is not None:
        line.occurred_at = occurred_at
    if proposed_type is not None:
        line.proposed_type = proposed_type
    if clear_contact:
        line.proposed_contact_id = None
    elif proposed_contact_id is not None:
        await validate_contact_in_org(db, org_id, proposed_contact_id)
        line.proposed_contact_id = proposed_contact_id

    if review_status is not None:
        line.review_status = review_status
    elif line.review_status == LineReviewStatus.PENDING and (
        clear_contact
        or any(
            v is not None
            for v in (merchant, amount_paise, occurred_at, proposed_type, proposed_contact_id)
        )
    ):
        line.review_status = LineReviewStatus.EDITED

    await db.flush()
    return line


async def bulk_set_review_status(
    db: AsyncSession,
    *,
    org_id: UUID,
    statement_id: UUID,
    review_status: LineReviewStatus,
    only_pending: bool = True,
) -> int:
    statement = await get_statement_or_404(db, org_id, statement_id)
    if statement.status == StatementStatus.IMPORTED:
        raise AppError(
            "Statement is already imported; review status is locked",
            code="statement_already_imported",
        )
    result = await db.execute(
        select(StatementLineCandidate).where(
            StatementLineCandidate.statement_id == statement_id,
            StatementLineCandidate.organization_id == org_id,
            StatementLineCandidate.committed_transaction_id.is_(None),
        )
    )
    lines = list(result.scalars().all())
    count = 0
    for line in lines:
        if only_pending and line.review_status == LineReviewStatus.REJECTED:
            continue
        if only_pending and line.review_status not in {
            LineReviewStatus.PENDING,
            LineReviewStatus.EDITED,
        }:
            continue
        line.review_status = review_status
        count += 1
    await db.flush()
    return count


def _posted_transaction_from_import_line(
    *,
    statement: Statement,
    line: StatementLineCandidate,
    user_id: UUID,
    account_id: UUID,
) -> Transaction:
    """Build a posted ledger row from a reviewed statement candidate.

    Always `PostingStatus.POSTED` — import confirm must never create drafts.
    """
    assert line.proposed_type is not None
    assert line.amount_paise is not None
    assert line.occurred_at is not None
    assert line.merchant is not None
    return Transaction(
        id=uuid4(),
        organization_id=statement.organization_id,
        account_id=account_id,
        credit_card_id=statement.credit_card_id,
        contact_id=line.proposed_contact_id,
        statement_id=statement.id,
        type=line.proposed_type,
        posting_status=PostingStatus.POSTED,
        amount_paise=line.amount_paise,
        currency="INR",
        occurred_at=line.occurred_at,
        merchant=line.merchant,
        category=None,
        notes=f"Imported from statement {statement.id}",
        created_by=user_id,
    )


async def import_statement(
    db: AsyncSession,
    *,
    statement: Statement,
    user_id: UUID,
    ip: str | None = None,
    ua: str | None = None,
) -> dict[str, int]:
    """Commit accepted/edited lines as posted transactions. Idempotent.

    Import confirm never creates drafts — candidates stay off the ledger until
    this path writes `posting_status=posted` rows only (FR-T9 / US-01.I5).
    """

    if statement.status == StatementStatus.IMPORTED:
        return {"created": 0, "skipped": 0}
    if statement.status in {
        StatementStatus.UPLOADED,
        StatementStatus.PARSING,
        StatementStatus.FAILED,
    }:
        raise AppError(
            "Statement is not ready for import. Parse and review first.",
            code="statement_not_ready",
        )

    account_id = await resolve_account_id_for_card(
        db,
        organization_id=statement.organization_id,
        credit_card_id=statement.credit_card_id,
    )

    result = await db.execute(
        select(StatementLineCandidate)
        .where(
            StatementLineCandidate.statement_id == statement.id,
            StatementLineCandidate.organization_id == statement.organization_id,
            StatementLineCandidate.review_status.in_(
                [LineReviewStatus.ACCEPTED, LineReviewStatus.EDITED]
            ),
            StatementLineCandidate.committed_transaction_id.is_(None),
        )
        .with_for_update()
    )
    lines = list(result.scalars().all())
    created = 0
    skipped = 0

    for line in lines:
        if (
            not line.merchant
            or not line.amount_paise
            or not line.occurred_at
            or not line.proposed_type
        ):
            skipped += 1
            continue
        tx = _posted_transaction_from_import_line(
            statement=statement,
            line=line,
            user_id=user_id,
            account_id=account_id,
        )
        db.add(tx)
        await db.flush()
        line.committed_transaction_id = tx.id
        created += 1

    # Mark imported if no pending lines remain uncommitted for accept/edit
    remaining = await db.execute(
        select(StatementLineCandidate).where(
            StatementLineCandidate.statement_id == statement.id,
            StatementLineCandidate.review_status.in_(
                [LineReviewStatus.ACCEPTED, LineReviewStatus.EDITED, LineReviewStatus.PENDING]
            ),
            StatementLineCandidate.committed_transaction_id.is_(None),
        )
    )
    pending_left = list(remaining.scalars().all())
    # If user only accepted some, still mark imported when no pending left
    still_pending = [
        line for line in pending_left if line.review_status == LineReviewStatus.PENDING
    ]
    still_to_import = [
        line
        for line in pending_left
        if line.review_status in {LineReviewStatus.ACCEPTED, LineReviewStatus.EDITED}
    ]

    if not still_pending and not still_to_import:
        statement.status = StatementStatus.IMPORTED
    elif created > 0 and not still_to_import:
        # Accepted ones done; may still have pending — keep needs_review
        statement.status = (
            StatementStatus.NEEDS_REVIEW if still_pending else StatementStatus.IMPORTED
        )
    elif created > 0:
        statement.status = StatementStatus.NEEDS_REVIEW

    # If everything was rejected or accepted+imported
    all_lines_result = await db.execute(
        select(StatementLineCandidate).where(StatementLineCandidate.statement_id == statement.id)
    )
    all_lines = list(all_lines_result.scalars().all())
    if all_lines and all(
        line.committed_transaction_id is not None or line.review_status == LineReviewStatus.REJECTED
        for line in all_lines
    ):
        statement.status = StatementStatus.IMPORTED

    await log_activity(
        db,
        action=ActivityAction.STATEMENT_IMPORT,
        summary=f"Imported {created} transactions from statement",
        actor_user_id=user_id,
        organization_id=statement.organization_id,
        resource_type="statement",
        resource_id=str(statement.id),
        ip_address=ip,
        user_agent=ua,
        metadata={"created": created, "skipped": skipped},
    )
    await db.flush()
    return {"created": created, "skipped": skipped}
