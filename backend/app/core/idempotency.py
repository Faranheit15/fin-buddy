"""Idempotency execution management (US-P05).

Provides RFC 9440 Idempotency-Key support, deterministic payload hashing,
row-level locking, response replay, and concurrency conflict handling.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from fastapi import Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, ConflictError
from app.models.idempotency import IdempotencyRecord

# RFC 9440 header name
IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_REPLAYED_HEADER = "Idempotency-Replayed"

# Key format: 16-128 characters, ASCII printable safe tokens (UUID, hex, alphanumeric)
IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_\-:.]{16,128}$")


def validate_idempotency_key(key: str) -> None:
    """Validate format and length of the idempotency key."""
    if not IDEMPOTENCY_KEY_PATTERN.match(key):
        raise AppError(
            "Idempotency-Key must be 16-128 characters containing only alphanumeric, hyphens, underscores, colons, or periods",
            code="invalid_idempotency_key",
            status_code=400,
        )


def to_jsonable(obj: Any) -> Any:
    """Recursively convert objects to JSON-serializable primitives."""
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(item) for item in obj]
    return obj


def compute_request_hash(path: str, payload: Any) -> str:
    """Compute SHA-256 digest of normalized path and payload."""
    jsonable = to_jsonable(payload)
    serialized = json.dumps(jsonable, sort_keys=True, separators=(",", ":"), default=str)
    normalized = f"{path}:{serialized}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


async def execute_idempotent[T](
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID | None,
    idempotency_key: str | None,
    request_path: str,
    payload: Any,
    action: Callable[[], Awaitable[tuple[int, T]]],
    response: Response | None = None,
    result_parser: Callable[[Any], T] | None = None,
) -> tuple[int, T]:
    """Execute a financial mutation with durable operation identity and replay protection.

    - If idempotency_key is None: executes action and commits normally.
    - If key provided:
      1. Validates key syntax.
      2. Checks for existing record under organization scope.
      3. If completed with matching payload: returns cached response (0 side effects).
      4. If key exists with different payload: raises 409 conflict.
      5. If in progress concurrently: raises 409 conflict.
      6. Inserts in_progress record, executes action, marks completed, commits atomically.
    """
    if not idempotency_key or not isinstance(idempotency_key, str):
        status_code, result = await action()
        await db.commit()
        return status_code, result

    key_clean = idempotency_key.strip()
    validate_idempotency_key(key_clean)
    req_hash = compute_request_hash(request_path, payload)

    # 1. Check for existing record
    stmt = (
        select(IdempotencyRecord)
        .where(
            IdempotencyRecord.organization_id == organization_id,
            IdempotencyRecord.idempotency_key == key_clean,
        )
        .with_for_update()
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()

    if existing is not None:
        if existing.request_hash != req_hash:
            raise ConflictError(
                "Idempotency key reused with different request payload",
                code="idempotency_payload_mismatch",
            )
        if existing.status == "completed":
            if response is not None:
                response.headers[IDEMPOTENCY_REPLAYED_HEADER] = "true"
                response.headers[IDEMPOTENCY_HEADER] = key_clean
            replayed_body = (
                result_parser(existing.response_body)
                if result_parser
                else existing.response_body
            )
            return existing.response_code or 200, replayed_body
        if existing.status == "in_progress":
            raise ConflictError(
                "Operation with this idempotency key is already in progress",
                code="idempotency_in_progress",
            )

    # 2. Record in-progress state
    record = IdempotencyRecord(
        id=uuid4(),
        organization_id=organization_id,
        user_id=user_id,
        idempotency_key=key_clean,
        request_path=request_path,
        request_hash=req_hash,
        status="in_progress",
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )
    db.add(record)

    try:
        await db.flush()
    except IntegrityError:
        # Concurrent collision on unique constraint (organization_id, idempotency_key)
        await db.rollback()
        retry_stmt = select(IdempotencyRecord).where(
            IdempotencyRecord.organization_id == organization_id,
            IdempotencyRecord.idempotency_key == key_clean,
        )
        existing = (await db.execute(retry_stmt)).scalar_one_or_none()
        if existing and existing.status == "completed":
            if existing.request_hash != req_hash:
                raise ConflictError(
                    "Idempotency key reused with different request payload",
                    code="idempotency_payload_mismatch",
                ) from None
            if response is not None:
                response.headers[IDEMPOTENCY_REPLAYED_HEADER] = "true"
                response.headers[IDEMPOTENCY_HEADER] = key_clean
            replayed_body = (
                result_parser(existing.response_body)
                if result_parser
                else existing.response_body
            )
            return existing.response_code or 200, replayed_body
        raise ConflictError(
            "Operation with this idempotency key is already in progress",
            code="idempotency_in_progress",
        ) from None

    # 3. Execute business mutation
    status_code, result = await action()

    # 4. Save response and transition to completed
    record.status = "completed"
    record.response_code = status_code
    record.response_body = to_jsonable(result)

    # 5. Commit atomically
    await db.commit()

    if response is not None:
        response.headers[IDEMPOTENCY_HEADER] = key_clean

    return status_code, result
