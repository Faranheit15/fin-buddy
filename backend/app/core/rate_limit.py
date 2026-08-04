"""Simple in-process rate limiting for auth and upload endpoints."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request
from starlette.responses import JSONResponse

from app.core.exceptions import AppError


class RateLimiter:
    """Fixed-window counter per key (IP + optional path bucket)."""

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, *, limit: int, window_seconds: float) -> None:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            q = self._hits[key]
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= limit:
                raise AppError(
                    "Too many requests. Please wait and try again.",
                    code="rate_limited",
                    status_code=429,
                    details={"retry_after_seconds": int(window_seconds)},
                )
            q.append(now)


_limiter = RateLimiter()


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def enforce_rate_limit(
    request: Request,
    *,
    bucket: str,
    limit: int,
    window_seconds: float = 60.0,
) -> None:
    """Raise AppError 429 when the client exceeds the limit for this bucket."""
    key = f"{bucket}:{client_ip(request)}"
    _limiter.check(key, limit=limit, window_seconds=window_seconds)


def rate_limit_response(exc: AppError) -> JSONResponse:
    retry = 60
    if isinstance(exc.details, dict) and "retry_after_seconds" in exc.details:
        retry = int(exc.details["retry_after_seconds"])
    return JSONResponse(
        status_code=429,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        headers={"Retry-After": str(retry)},
    )


# Shared limits for personal production (tune via Settings later if needed)
AUTH_LIMIT = 30  # per IP per minute across auth routes
UPLOAD_LIMIT = 10  # statement uploads per IP per minute
