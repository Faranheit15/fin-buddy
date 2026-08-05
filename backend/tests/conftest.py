"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("AUTO_MIGRATE", "false")
    monkeypatch.setenv("AUTO_SEED", "false")
    monkeypatch.setenv("LOG_API_REQUESTS", "false")
    # Override process env AND .env file values for unit tests
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    # Import after env is set
    from app.main import create_app

    application = create_app()
    with TestClient(application) as test_client:
        yield test_client
