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


def _generate_test_ec_key():
    from cryptography.hazmat.primitives.asymmetric import ec

    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key, private_key.public_key()


def test_decode_valid_es256_token_via_jwks() -> None:
    from unittest.mock import MagicMock, patch

    priv, pub = _generate_test_ec_key()
    kid = "test-kid-es256-1"
    sub_id = str(uuid4())

    token = jwt.encode(
        {
            "sub": sub_id,
            "email": "user@example.com",
            "aud": "authenticated",
            "iss": "https://testproj.supabase.co/auth/v1",
            "exp": datetime.now(UTC) + timedelta(minutes=10),
        },
        priv,
        algorithm="ES256",
        headers={"kid": kid},
    )

    mock_client = MagicMock()
    mock_key = MagicMock()
    mock_key.key = pub
    mock_client.get_signing_key_from_jwt.return_value = mock_key

    with patch("app.core.security.get_jwks_client", return_value=mock_client):
        settings = Settings(
            supabase_url="https://testproj.supabase.co",
            jwt_verification_mode="jwks_only",
        )
        claims = decode_supabase_jwt(token, settings)
        assert claims["sub"] == sub_id
        assert claims["email"] == "user@example.com"


def test_temporary_hs256_compatibility_in_dev() -> None:
    secret = "test-secret-with-32-bytes-minimum"
    sub_id = str(uuid4())
    settings = Settings(
        environment="development",
        jwt_verification_mode="hybrid",
        supabase_jwt_secret=secret,
        supabase_jwt_issuer="https://testproj.supabase.co/auth/v1",
    )
    token = jwt.encode(
        {
            "sub": sub_id,
            "aud": "authenticated",
            "iss": "https://testproj.supabase.co/auth/v1",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        secret,
        algorithm="HS256",
    )
    claims = decode_supabase_jwt(token, settings)
    assert claims["sub"] == sub_id


def test_production_rejects_hs256_tokens() -> None:
    secret = "test-secret-with-32-bytes-minimum"
    settings = Settings(
        environment="production",
        jwt_verification_mode="jwks_only",
        database_url="postgresql://localhost:5432/db",
        supabase_url="https://testproj.supabase.co",
        supabase_publishable_key="sb_publishable_test123",
        supabase_service_role_key="test-key",
        debug=False,
        demo_auth_enabled=False,
        auto_migrate=False,
        auto_seed=False,
        statement_storage_backend="supabase",
        statement_storage_bucket="statements",
    )
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "aud": "authenticated",
            "iss": "https://testproj.supabase.co/auth/v1",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        secret,
        algorithm="HS256",
    )
    with pytest.raises(UnauthorizedError, match="HS256 tokens are rejected in production"):
        decode_supabase_jwt(token, settings)


def test_es256_unknown_kid_rejected() -> None:
    from unittest.mock import MagicMock, patch

    from jwt import PyJWKSetError

    priv, _ = _generate_test_ec_key()
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "aud": "authenticated",
            "iss": "https://testproj.supabase.co/auth/v1",
            "exp": datetime.now(UTC) + timedelta(minutes=10),
        },
        priv,
        algorithm="ES256",
        headers={"kid": "unknown-kid"},
    )

    mock_client = MagicMock()
    mock_client.get_signing_key_from_jwt.side_effect = PyJWKSetError("Key not found")

    with patch("app.core.security.get_jwks_client", return_value=mock_client):
        settings = Settings(
            supabase_url="https://testproj.supabase.co",
            jwt_verification_mode="jwks_only",
        )
        with pytest.raises(UnauthorizedError, match="Invalid ES256 token"):
            decode_supabase_jwt(token, settings)


def test_es256_expired_token_rejected() -> None:
    from unittest.mock import MagicMock, patch

    priv, pub = _generate_test_ec_key()
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "aud": "authenticated",
            "iss": "https://testproj.supabase.co/auth/v1",
            "exp": datetime.now(UTC) - timedelta(minutes=5),
        },
        priv,
        algorithm="ES256",
        headers={"kid": "test-kid-1"},
    )

    mock_client = MagicMock()
    mock_key = MagicMock()
    mock_key.key = pub
    mock_client.get_signing_key_from_jwt.return_value = mock_key

    with patch("app.core.security.get_jwks_client", return_value=mock_client):
        settings = Settings(
            supabase_url="https://testproj.supabase.co",
            jwt_verification_mode="jwks_only",
        )
        with pytest.raises(UnauthorizedError, match="expired"):
            decode_supabase_jwt(token, settings)


def test_es256_wrong_audience_rejected() -> None:
    from unittest.mock import MagicMock, patch

    priv, pub = _generate_test_ec_key()
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "aud": "wrong-audience",
            "iss": "https://testproj.supabase.co/auth/v1",
            "exp": datetime.now(UTC) + timedelta(minutes=10),
        },
        priv,
        algorithm="ES256",
        headers={"kid": "test-kid-1"},
    )

    mock_client = MagicMock()
    mock_key = MagicMock()
    mock_key.key = pub
    mock_client.get_signing_key_from_jwt.return_value = mock_key

    with patch("app.core.security.get_jwks_client", return_value=mock_client):
        settings = Settings(
            supabase_url="https://testproj.supabase.co",
            jwt_verification_mode="jwks_only",
        )
        with pytest.raises(UnauthorizedError, match=r"(?i)audience"):
            decode_supabase_jwt(token, settings)


def test_es256_wrong_issuer_rejected() -> None:
    from unittest.mock import MagicMock, patch

    priv, pub = _generate_test_ec_key()
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "aud": "authenticated",
            "iss": "https://attacker.supabase.co/auth/v1",
            "exp": datetime.now(UTC) + timedelta(minutes=10),
        },
        priv,
        algorithm="ES256",
        headers={"kid": "test-kid-1"},
    )

    mock_client = MagicMock()
    mock_key = MagicMock()
    mock_key.key = pub
    mock_client.get_signing_key_from_jwt.return_value = mock_key

    with patch("app.core.security.get_jwks_client", return_value=mock_client):
        settings = Settings(
            supabase_url="https://testproj.supabase.co",
            jwt_verification_mode="jwks_only",
        )
        with pytest.raises(UnauthorizedError, match=r"(?i)issuer"):
            decode_supabase_jwt(token, settings)


def test_unsupported_algorithm_rejected() -> None:
    settings = Settings(
        supabase_url="https://testproj.supabase.co",
        jwt_verification_mode="jwks_only",
    )
    # Mint token with header alg="none"
    header = jwt.utils.base64url_encode(b'{"alg":"none","typ":"JWT"}').decode("utf-8")
    payload = jwt.utils.base64url_encode(b'{"sub":"123","aud":"authenticated"}').decode("utf-8")
    token = f"{header}.{payload}."

    with pytest.raises(UnauthorizedError, match="Unsupported token algorithm"):
        decode_supabase_jwt(token, settings)


def test_is_opaque_supabase_key_helper() -> None:
    from app.core.security import is_opaque_supabase_key

    assert is_opaque_supabase_key("sb_publishable_abcdef123456") is True
    assert is_opaque_supabase_key("sb_secret_abcdef123456") is True
    assert is_opaque_supabase_key("sbp_abcdef123456") is True
    assert is_opaque_supabase_key("sbs_abcdef123456") is True
    assert is_opaque_supabase_key("opaque_key_without_jwt_dots") is True
    assert is_opaque_supabase_key(None) is False
    assert is_opaque_supabase_key("") is False

    # Legacy 3-part base64url JWT keys
    legacy_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiJ9.signature_part"
    assert is_opaque_supabase_key(legacy_jwt) is False
