"""Security regression tests for trust boundaries."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.config import Settings
from app.core.exceptions import UnauthorizedError
from app.core.request_meta import client_ip, redacted_query_string
from app.core.security import decode_supabase_jwt, require_job_runner


def _request(*, forwarded_for: str | None = None) -> Request:
    headers = [] if forwarded_for is None else [(b"x-forwarded-for", forwarded_for.encode())]
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": headers,
            "client": ("127.0.0.1", 12345),
            "server": ("test", 80),
        }
    )


def test_forwarded_ip_is_only_trusted_from_configured_proxy() -> None:
    request = _request(forwarded_for="203.0.113.10, 10.0.0.1")
    assert client_ip(request, Settings()) == "127.0.0.1"
    assert client_ip(request, Settings(trusted_proxy_ips=["127.0.0.1"])) == "203.0.113.10"


def test_jwt_issuer_must_exactly_match_configured_supabase_issuer() -> None:
    secret = "test-secret-with-32-bytes-minimum"
    settings = Settings(
        supabase_jwt_secret=secret,
        supabase_jwt_issuer="https://project.supabase.co/auth/v1",
    )
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "aud": "authenticated",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
            "iss": "https://project.supabase.co",
        },
        secret,
        algorithm="HS256",
    )

    with pytest.raises(UnauthorizedError, match="issuer"):
        decode_supabase_jwt(token, settings)


def test_scheduled_job_requires_a_secret() -> None:
    request = _request()
    with pytest.raises(HTTPException) as exc_info:
        require_job_runner(request, Settings())
    assert exc_info.value.status_code == 503

    with pytest.raises(UnauthorizedError):
        require_job_runner(request, Settings(job_runner_secret="expected-secret"))

    authorized = _request()
    authorized.scope["headers"] = [(b"x-job-secret", b"expected-secret")]
    require_job_runner(authorized, Settings(job_runner_secret="expected-secret"))


def test_query_values_are_redacted_before_request_logging() -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "scheme": "https",
            "path": "/v1/statements",
            "query_string": b"email=alice%40example.com&token=secret",
            "headers": [],
            "client": ("203.0.113.9", 443),
            "server": ("api.example.com", 443),
        }
    )

    assert redacted_query_string(request) == "email=%5BREDACTED%5D&token=%5BREDACTED%5D"
