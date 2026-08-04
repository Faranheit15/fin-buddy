"""Rate limiter unit tests."""

from starlette.requests import Request

from app.core.exceptions import AppError
from app.core.rate_limit import RateLimiter, enforce_rate_limit


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = RateLimiter()
    for _ in range(3):
        limiter.check("ip:test", limit=3, window_seconds=60.0)
    try:
        limiter.check("ip:test", limit=3, window_seconds=60.0)
        raise AssertionError("expected rate limit")
    except AppError as exc:
        assert exc.status_code == 429
        assert exc.code == "rate_limited"


def test_enforce_rate_limit_uses_forwarded_ip() -> None:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/v1/auth/login",
        "raw_path": b"/api/v1/auth/login",
        "query_string": b"",
        "headers": [(b"x-forwarded-for", b"203.0.113.10, 10.0.0.1")],
        "client": ("127.0.0.1", 12345),
        "server": ("test", 80),
    }
    request = Request(scope)
    for _ in range(2):
        enforce_rate_limit(request, bucket="unit-test-auth", limit=2, window_seconds=60.0)
    try:
        enforce_rate_limit(request, bucket="unit-test-auth", limit=2, window_seconds=60.0)
        raise AssertionError("expected rate limit")
    except AppError as exc:
        assert exc.status_code == 429
