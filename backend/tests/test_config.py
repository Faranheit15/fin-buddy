"""Settings helpers."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_async_and_sync_urls() -> None:
    settings = Settings(
        database_url="postgresql://user:pass@localhost:5432/finbuddy",
    )
    assert settings.async_database_url().startswith("postgresql+asyncpg://")
    assert settings.sync_database_url().startswith("postgresql+psycopg://")


def test_jwt_issuer_derived() -> None:
    settings = Settings(supabase_url="https://abc.supabase.co")
    assert settings.supabase_jwt_issuer == "https://abc.supabase.co/auth/v1"


TEST_DB = "postgresql://localhost:5432/testdb"
TEST_URL = "https://xyz.supabase.co"
TEST_ROLE = "test-role-key"
TEST_JWT = "test-jwt-secret-value-32chars-long"


def test_production_valid_configuration() -> None:
    settings = Settings(
        environment="production",
        debug=False,
        demo_auth_enabled=False,
        auto_migrate=False,
        auto_seed=False,
        statement_storage_backend="supabase",
        statement_storage_bucket="statements",
        database_url=TEST_DB,
        supabase_url=TEST_URL,
        supabase_service_role_key=TEST_ROLE,
        supabase_jwt_secret=TEST_JWT,
    )
    assert settings.is_production is True
    assert settings.demo_login_allowed is False


@pytest.mark.parametrize(
    "override,expected_error_substr",
    [
        ({"debug": True}, "DEBUG=false"),
        ({"demo_auth_enabled": True}, "DEMO_AUTH_ENABLED=false"),
        ({"auto_migrate": True}, "AUTO_MIGRATE=false"),
        ({"auto_seed": True}, "AUTO_SEED=false"),
        ({"statement_storage_backend": "local"}, "STATEMENT_STORAGE_BACKEND=supabase"),
        ({"statement_storage_bucket": ""}, "STATEMENT_STORAGE_BUCKET"),
        ({"database_url": None}, "DATABASE_URL"),
        ({"supabase_url": None}, "SUPABASE_URL"),
        ({"supabase_service_role_key": None}, "SUPABASE_SERVICE_ROLE_KEY"),
        ({"supabase_jwt_secret": None}, "SUPABASE_JWT_SECRET"),
        ({"supabase_jwt_secret": "fin-buddy-demo-dev-secret-change-me"}, "strong, non-default"),
        ({"supabase_jwt_secret": "short"}, "strong, non-default"),
    ],
)
def test_production_fails_closed(override: dict[str, object], expected_error_substr: str) -> None:
    base_prod_kwargs: dict[str, object] = {
        "environment": "production",
        "debug": False,
        "demo_auth_enabled": False,
        "auto_migrate": False,
        "auto_seed": False,
        "statement_storage_backend": "supabase",
        "statement_storage_bucket": "statements",
        "database_url": TEST_DB,
        "supabase_url": TEST_URL,
        "supabase_service_role_key": TEST_ROLE,
        "supabase_jwt_secret": TEST_JWT,
    }
    base_prod_kwargs.update(override)
    with pytest.raises(ValidationError) as exc_info:
        Settings(**base_prod_kwargs)  # type: ignore[arg-type]
    assert expected_error_substr in str(exc_info.value)


def test_development_defaults_usable() -> None:
    settings = Settings(environment="development")
    assert settings.is_production is False
    assert settings.demo_login_allowed is True
