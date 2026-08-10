"""Shared Supabase Postgres rate limiting with a bounded development fallback."""

from __future__ import annotations

import hashlib
import time
from collections import defaultdict, deque
from datetime import UTC, datetime
from threading import Lock

from fastapi import Request
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.request_meta import client_ip as trusted_client_ip
from app.db.session import get_async_session_factory
from app.models.rate_limit import RateLimitWindow


class RateLimiter:
    """Bounded in-process fallback for development and tests only."""

    def __init__(self, *, max_keys: int = 10_000) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()
        self._max_keys = max_keys
        self._last_sweep = 0.0

    def check(self, key: str, *, limit: int, window_seconds: float) -> None:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            self._prune(now, cutoff)
            if key not in self._hits and len(self._hits) >= self._max_keys:
                self._hits.pop(next(iter(self._hits)), None)
            hits = self._hits[key]
            while hits and hits[0] < cutoff:
                hits.popleft()
            if len(hits) >= limit:
                raise _rate_limited(window_seconds)
            hits.append(now)

    def _prune(self, now: float, cutoff: float) -> None:
        if len(self._hits) < self._max_keys and now - self._last_sweep < 60:
            return
        self._last_sweep = now
        for key, hits in list(self._hits.items()):
            while hits and hits[0] < cutoff:
                hits.popleft()
            if not hits:
                del self._hits[key]


_limiter = RateLimiter()
_last_database_prune = 0.0


def _rate_limited(window_seconds: float) -> AppError:
    return AppError(
        "Too many requests. Please wait and try again.",
        code="rate_limited",
        status_code=429,
        details={"retry_after_seconds": int(window_seconds)},
    )


def client_ip(request: Request) -> str:
    return trusted_client_ip(request) or "unknown"


def _key(bucket: str, address: str, window: int) -> str:
    return hashlib.sha256(f"{bucket}:{address}:{window}".encode()).hexdigest()


async def _database_check(*, bucket: str, address: str, limit: int, window_seconds: float) -> None:
    global _last_database_prune
    now = datetime.now(UTC)
    window = int(now.timestamp() // window_seconds)
    expires_at = datetime.fromtimestamp((window + 1) * window_seconds, UTC)
    key_hash = _key(bucket, address, window)
    factory = get_async_session_factory()

    try:
        async with factory() as session:
            statement = (
                insert(RateLimitWindow)
                .values(
                    key_hash=key_hash,
                    bucket=bucket,
                    hit_count=1,
                    expires_at=expires_at,
                )
                .on_conflict_do_update(
                    index_elements=[RateLimitWindow.key_hash],
                    set_={"hit_count": RateLimitWindow.hit_count + 1},
                )
                .returning(RateLimitWindow.hit_count)
            )
            count = await session.scalar(statement)
            if time.monotonic() - _last_database_prune > 300:
                await session.execute(
                    delete(RateLimitWindow).where(RateLimitWindow.expires_at < now)
                )
                _last_database_prune = time.monotonic()
            await session.commit()
    except Exception as exc:
        raise AppError(
            "Rate limiter is temporarily unavailable",
            code="rate_limiter_unavailable",
            status_code=503,
        ) from exc

    if count is None:
        raise AppError(
            "Rate limiter is temporarily unavailable",
            code="rate_limiter_unavailable",
            status_code=503,
        )
    if count > limit:
        raise _rate_limited(window_seconds)


async def enforce_rate_limit(
    request: Request,
    *,
    bucket: str,
    limit: int,
    window_seconds: float = 60.0,
) -> None:
    """Raise a 429 when a shared production or bounded local bucket is exhausted."""
    settings = get_settings()
    address = client_ip(request)
    if not settings.database_configured:
        if settings.is_production:
            raise AppError(
                "Rate limiter is not configured",
                code="rate_limiter_unavailable",
                status_code=503,
            )
        _limiter.check(f"{bucket}:{address}", limit=limit, window_seconds=window_seconds)
        return
    await _database_check(
        bucket=bucket,
        address=address,
        limit=limit,
        window_seconds=window_seconds,
    )


def rate_limit_response(exc: AppError) -> JSONResponse:
    retry = 60
    if isinstance(exc.details, dict) and "retry_after_seconds" in exc.details:
        retry = int(exc.details["retry_after_seconds"])
    headers = {"Retry-After": str(retry)} if exc.status_code == 429 else None
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        headers=headers,
    )


AUTH_LIMIT = 30
UPLOAD_LIMIT = 10
