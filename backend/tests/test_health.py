"""Health and readiness endpoint tests."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings


def test_health_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app"] == "Fin Buddy API"
    assert "version" in body


def test_health_unaffected_by_db_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
    get_settings.cache_clear()
    with patch(
        "app.api.v1.health.get_async_session_factory",
        side_effect=OperationalError("connection refused", None, None),
    ):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_ready_dev_unconfigured_returns_200(client: TestClient) -> None:
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_healthy_returns_200(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
    get_settings.cache_clear()

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    with patch("app.api.v1.health.get_async_session_factory", return_value=mock_factory):
        response = client.get("/api/v1/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["app"] == "Fin Buddy API"


def test_ready_db_failure_returns_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
    get_settings.cache_clear()

    mock_session = AsyncMock()
    mock_session.execute.side_effect = OperationalError(
        "connection refused to db.internal:5432", None, None
    )
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    with patch("app.api.v1.health.get_async_session_factory", return_value=mock_factory):
        response = client.get("/api/v1/ready")
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "degraded"
        assert "db.internal" not in response.text
        assert "connection refused" not in response.text
        assert "postgresql" not in response.text


def test_ready_timeout_returns_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
    get_settings.cache_clear()

    mock_session = AsyncMock()
    mock_session.execute.side_effect = TimeoutError("query timeout")
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    with patch("app.api.v1.health.get_async_session_factory", return_value=mock_factory):
        response = client.get("/api/v1/ready")
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "degraded"
        assert "timeout" not in response.text


def test_ready_unconfigured_in_staging_returns_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("DATABASE_URL", "")
    get_settings.cache_clear()

    response = client.get("/api/v1/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["environment"] == "staging"


def test_ready_unconfigured_in_production_returns_503(client: TestClient) -> None:
    from app.api.v1.health import get_settings

    # Using dependency override to safely test production mode without requiring real cloud secrets
    mock_settings = MagicMock()
    mock_settings.database_configured = False
    mock_settings.environment = "production"
    mock_settings.app_name = "Fin Buddy API"
    mock_settings.app_version = "0.1.0"

    client.app.dependency_overrides[get_settings] = lambda: mock_settings
    try:
        response = client.get("/api/v1/ready")
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "degraded"
        assert body["environment"] == "production"
    finally:
        client.app.dependency_overrides.pop(get_settings, None)


@pytest.mark.asyncio
async def test_probes_skip_request_logging(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LOG_API_REQUESTS", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
    get_settings.cache_clear()

    with patch("app.core.middleware.log_api_request", new_callable=AsyncMock) as mock_log:
        client.get("/api/v1/health")
        client.get("/api/v1/ready")
        await asyncio.sleep(0.01)
        mock_log.assert_not_called()


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "health" in data
    assert data.get("docs") == "/docs"
