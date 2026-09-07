"""Authentication redirects and PKCE OAuth flow verification."""

from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.exceptions import AppError
from app.models.enums import OrgRole, PlatformRole
from app.models.organization import Organization
from app.models.profile import Profile
from app.services.auth_service import (
    _frontend_callback_url,
    google_oauth_url,
    validate_safe_destination,
)


def test_auth_redirect_accepts_only_the_configured_callback() -> None:
    settings = Settings(frontend_app_url="https://app.example.com")
    assert (
        _frontend_callback_url(settings, "https://app.example.com/auth/callback")
        == "https://app.example.com/auth/callback"
    )


def test_auth_redirect_defaults_to_configured_callback_when_omitted() -> None:
    settings = Settings(frontend_app_url="https://app.example.com")
    assert _frontend_callback_url(settings, None) == "https://app.example.com/auth/callback"


@pytest.mark.parametrize(
    "candidate",
    [
        "https://evil.example/auth/callback",
        "https://app.example.com/other",
        "https://app.example.com/auth/callback?next=/app",
        "https://app.example.com/auth/callback?next=https://evil.example",
        "https://app.example.com/auth/callback#access_token=secret",
        "http://app.example.com/auth/callback",
        "https://app.example.com:8443/auth/callback",
        "//evil.example/auth/callback",
        "https://app.example.com/auth/../evil",
        "https://app.example.com/auth/%2e%2e/evil",
        "javascript:alert(1)",
    ],
)
def test_auth_redirect_rejects_untrusted_destination(candidate: str) -> None:
    settings = Settings(frontend_app_url="https://app.example.com")
    with pytest.raises(AppError, match="Invalid authentication redirect URL"):
        _frontend_callback_url(settings, candidate)


def test_google_oauth_url_builder() -> None:
    settings = Settings(
        supabase_url="https://test.supabase.co",
        frontend_app_url="https://fin-buddy-dev.vercel.app",
    )
    url = google_oauth_url(
        settings,
        redirect_to="https://fin-buddy-dev.vercel.app/auth/callback",
        code_challenge="dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
        code_challenge_method="s256",
        state="safe-state-12345678",
    )
    assert url.startswith("https://test.supabase.co/auth/v1/authorize?")
    assert "provider=google" in url
    assert "redirect_to=https%3A%2F%2Ffin-buddy-dev.vercel.app%2Fauth%2Fcallback" in url
    assert "code_challenge=dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk" in url
    assert "code_challenge_method=s256" in url
    assert "state=" not in url


@pytest.mark.parametrize(
    ("challenge", "method"),
    [
        ("short", "s256"),
        ("toolong" * 30, "s256"),
        ("invalid@challenge!", "s256"),
        ("dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk", "plain"),
        ("dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk", "none"),
    ],
)
def test_google_oauth_url_rejects_invalid_code_challenge(challenge: str, method: str) -> None:
    settings = Settings(
        supabase_url="https://test.supabase.co",
        frontend_app_url="https://fin-buddy-dev.vercel.app",
    )
    with pytest.raises(AppError):
        google_oauth_url(
            settings,
            code_challenge=challenge,
            code_challenge_method=method,
        )


@pytest.mark.parametrize(
    "bad_state",
    [
        "short",
        "state with spaces",
        "state<script>",
        "state\r\nattack",
        "a" * 300,
    ],
)
def test_google_oauth_url_rejects_invalid_state(bad_state: str) -> None:
    settings = Settings(
        supabase_url="https://test.supabase.co",
        frontend_app_url="https://fin-buddy-dev.vercel.app",
    )
    with pytest.raises(AppError, match="Invalid OAuth state"):
        google_oauth_url(settings, state=bad_state)


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (None, "/app"),
        ("", "/app"),
        ("   ", "/app"),
        ("/app", "/app"),
        ("/app/cards", "/app/cards"),
        ("/app/cards/123", "/app/cards/123"),
        ("/app/accounts?filter=open", "/app/accounts?filter=open"),
        ("/app#fragment", "/app"),
        ("/app/cards#section", "/app"),
        ("https://evil.example", "/app"),
        ("https://evil.example/app", "/app"),
        ("http://localhost:3000/app", "/app"),
        ("//evil.example/app", "/app"),
        ("/\\evil.example", "/app"),
        ("\\\\evil.example", "/app"),
        ("/app/../../evil", "/app"),
        ("/app/%2e%2e/evil", "/app"),
        ("/app/../accounts", "/app"),
        ("/settings", "/app"),
        ("/login", "/app"),
        ("/auth/callback", "/app"),
        ("javascript:alert(1)", "/app"),
        ("data:text/html,test", "/app"),
        ("/app\r\nSet-Cookie:bad", "/app"),
    ],
)
def test_validate_safe_destination(candidate: str | None, expected: str) -> None:
    assert validate_safe_destination(candidate) == expected


def test_oauth_google_api_endpoint_success(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "sb_publishable_test123456")
    monkeypatch.setenv("FRONTEND_APP_URL", "https://fin-buddy-dev.vercel.app")
    from app.core.config import get_settings

    get_settings.cache_clear()

    response = client.get(
        "/api/v1/auth/oauth/google",
        params={
            "redirect_to": "https://fin-buddy-dev.vercel.app/auth/callback",
            "code_challenge": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
            "code_challenge_method": "s256",
            "state": "random_test_state_12345",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert "apikey=sb_publishable_test123456" in data["url"]
    assert "provider=google" in data["url"]
    assert "code_challenge=dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk" in data["url"]
    # State must NOT be in Supabase authorize URL to prevent bad_oauth_state
    assert "state=" not in data["url"]


def test_oauth_google_api_endpoint_rejects_query_regression(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "sb_publishable_test123456")
    monkeypatch.setenv("FRONTEND_APP_URL", "https://fin-buddy-dev.vercel.app")
    from app.core.config import get_settings

    get_settings.cache_clear()

    response = client.get(
        "/api/v1/auth/oauth/google",
        params={
            "redirect_to": "https://fin-buddy-dev.vercel.app/auth/callback?next=/app",
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_redirect"


def test_session_endpoint_rejects_implicit_tokens(client: TestClient) -> None:
    """POST /api/v1/auth/session must strictly reject access_token and enforce PKCE code."""
    async def mock_db():
        yield AsyncMock()

    from app.db.session import get_db

    client.app.dependency_overrides[get_db] = mock_db
    try:
        response = client.post(
            "/api/v1/auth/session",
            json={
                "access_token": "some-implicit-access-token-12345",
                "refresh_token": "some-refresh-token",
            },
        )
        # Pydantic validation failure: missing code and code_verifier
        assert response.status_code == 422
    finally:
        client.app.dependency_overrides.clear()


def test_session_endpoint_rejects_short_code_verifier(client: TestClient) -> None:
    async def mock_db():
        yield AsyncMock()

    from app.db.session import get_db

    client.app.dependency_overrides[get_db] = mock_db
    try:
        response = client.post(
            "/api/v1/auth/session",
            json={
                "code": "test-auth-code-123",
                "code_verifier": "too-short",
            },
        )
        assert response.status_code == 422
    finally:
        client.app.dependency_overrides.clear()


def test_session_endpoint_pkce_exchange_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def mock_db():
        yield AsyncMock()

    from app.db.session import get_db

    client.app.dependency_overrides[get_db] = mock_db

    from datetime import UTC, datetime

    user_id = uuid4()
    org_id = uuid4()
    mock_profile = Profile(
        id=user_id,
        email="testuser@example.com",
        platform_role=PlatformRole.USER,
        is_active=True,
        timezone="Asia/Kolkata",
        due_soon_days=7,
        high_utilization_percent=80,
        created_at=datetime.now(UTC),
    )
    mock_org = Organization(id=org_id, name="Personal", slug="personal")

    mock_tokens: dict[str, Any] = {
        "access_token": "mock-supabase-access-token-12345",
        "refresh_token": "mock-supabase-refresh-token-12345",
        "expires_in": 3600,
        "expires_at": 1800000000,
        "token_type": "bearer",
    }

    try:
        with patch(
            "app.services.auth_service.session_from_code",
            new=AsyncMock(return_value=(mock_profile, mock_org, mock_tokens)),
        ), patch(
            "app.api.v1.auth._membership_role",
            new=AsyncMock(return_value=OrgRole.OWNER),
        ):
            response = client.post(
                "/api/v1/auth/session",
                json={
                    "code": "valid-supabase-auth-code-12345",
                    "code_verifier": "a" * 43,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["user"]["id"] == str(user_id)
            assert data["organization"]["id"] == str(org_id)
            assert data["session"]["access_token"] == "mock-supabase-access-token-12345"
            assert data["message"] == "Session established"
    finally:
        client.app.dependency_overrides.clear()


def test_session_endpoint_pkce_exchange_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def mock_db():
        yield AsyncMock()

    from app.db.session import get_db

    client.app.dependency_overrides[get_db] = mock_db
    try:
        with patch(
            "app.services.auth_service.session_from_code",
            new=AsyncMock(
                side_effect=AppError("Authorization code expired", code="invalid_grant", status_code=400)
            ),
        ):
            response = client.post(
                "/api/v1/auth/session",
                json={
                    "code": "expired-code",
                    "code_verifier": "b" * 43,
                },
            )
            assert response.status_code == 400
            assert response.json()["error"]["code"] == "invalid_grant"
    finally:
        client.app.dependency_overrides.clear()
