"""Rate limiter unit tests."""

import pytest
from starlette.requests import Request

from app.core.config import Settings
from app.core.exceptions import AppError
from app.core.rate_limit import RateLimiter, enforce_rate_limit


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = RateLimiter()
    for _ in range(3):
        limiter.check("ip:test", limit=3, window_seconds=60.0)
    with pytest.raises(AppError) as exc_info:
        limiter.check("ip:test", limit=3, window_seconds=60.0)
    assert exc_info.value.status_code == 429
    assert exc_info.value.code == "rate_limited"


@pytest.mark.asyncio
async def test_enforce_rate_limit_uses_bounded_development_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.core.rate_limit.get_settings", lambda: Settings(environment="test"))
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/v1/auth/login",
        "raw_path": b"/api/v1/auth/login",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("test", 80),
    }
    request = Request(scope)
    for _ in range(2):
        await enforce_rate_limit(request, bucket="unit-test-auth", limit=2, window_seconds=60.0)
    with pytest.raises(AppError) as exc_info:
        await enforce_rate_limit(request, bucket="unit-test-auth", limit=2, window_seconds=60.0)
    assert exc_info.value.status_code == 429
