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
TEST_PUBLISHABLE = "sb_publishable_test123456"
TEST_ANON = "test-anon-legacy-key"


def test_production_valid_configuration() -> None:
    settings = Settings(
        environment="production",
        jwt_verification_mode="jwks_only",
        debug=False,
        demo_auth_enabled=False,
        auto_migrate=False,
        auto_seed=False,
        statement_storage_backend="supabase",
        statement_storage_bucket="statements",
        database_url=TEST_DB,
        supabase_url=TEST_URL,
        supabase_publishable_key=TEST_PUBLISHABLE,
        supabase_service_role_key=TEST_ROLE,
    )
    assert settings.is_production is True
    assert settings.demo_login_allowed is False
    assert settings.supabase_jwks_url == f"{TEST_URL}/auth/v1/.well-known/jwks.json"
    assert settings.effective_supabase_publishable_key == TEST_PUBLISHABLE
    assert settings.supabase_anon_key == TEST_PUBLISHABLE  # Reconciled alias


@pytest.mark.parametrize(
    "override,expected_error_substr",
    [
        ({"jwt_verification_mode": "hybrid"}, "jwt_verification_mode='jwks_only'"),
        ({"debug": True}, "DEBUG=false"),
        ({"demo_auth_enabled": True}, "DEMO_AUTH_ENABLED=false"),
        ({"auto_migrate": True}, "AUTO_MIGRATE=false"),
        ({"auto_seed": True}, "AUTO_SEED=false"),
        ({"statement_storage_backend": "local"}, "STATEMENT_STORAGE_BACKEND=supabase"),
        ({"statement_storage_bucket": ""}, "STATEMENT_STORAGE_BUCKET"),
        ({"database_url": None}, "DATABASE_URL"),
        ({"supabase_url": None}, "SUPABASE_URL"),
        ({"supabase_service_role_key": None}, "SUPABASE_SERVICE_ROLE_KEY"),
        ({"supabase_publishable_key": None, "supabase_anon_key": None}, "SUPABASE_PUBLISHABLE_KEY"),
        ({"supabase_jwt_secret": "fin-buddy-demo-dev-secret-change-me"}, "strong, non-default"),
        ({"supabase_jwt_secret": "short"}, "strong, non-default"),
    ],
)
def test_production_fails_closed(override: dict[str, object], expected_error_substr: str) -> None:
    base_prod_kwargs: dict[str, object] = {
        "environment": "production",
        "jwt_verification_mode": "jwks_only",
        "debug": False,
        "demo_auth_enabled": False,
        "auto_migrate": False,
        "auto_seed": False,
        "statement_storage_backend": "supabase",
        "statement_storage_bucket": "statements",
        "database_url": TEST_DB,
        "supabase_url": TEST_URL,
        "supabase_publishable_key": TEST_PUBLISHABLE,
        "supabase_service_role_key": TEST_ROLE,
    }
    base_prod_kwargs.update(override)
    with pytest.raises(ValidationError) as exc_info:
        Settings(**base_prod_kwargs)  # type: ignore[arg-type]
    assert expected_error_substr in str(exc_info.value)


def test_supabase_publishable_key_reconciliation() -> None:
    settings = Settings(supabase_publishable_key="sb_publishable_123")
    assert settings.supabase_publishable_key == "sb_publishable_123"
    assert settings.supabase_anon_key == "sb_publishable_123"
    assert settings.effective_supabase_publishable_key == "sb_publishable_123"


def test_supabase_anon_key_compatibility_alias() -> None:
    settings = Settings(supabase_anon_key="legacy_anon_jwt_or_key")
    assert settings.supabase_anon_key == "legacy_anon_jwt_or_key"
    assert settings.supabase_publishable_key == "legacy_anon_jwt_or_key"
    assert settings.effective_supabase_publishable_key == "legacy_anon_jwt_or_key"


def test_production_accepts_anon_key_alias() -> None:
    settings = Settings(
        environment="production",
        jwt_verification_mode="jwks_only",
        debug=False,
        demo_auth_enabled=False,
        auto_migrate=False,
        auto_seed=False,
        statement_storage_backend="supabase",
        statement_storage_bucket="statements",
        database_url=TEST_DB,
        supabase_url=TEST_URL,
        supabase_anon_key=TEST_ANON,
        supabase_service_role_key=TEST_ROLE,
    )
    assert settings.is_production is True
    assert settings.effective_supabase_publishable_key == TEST_ANON
    assert settings.supabase_publishable_key == TEST_ANON


def test_development_defaults_usable() -> None:
    settings = Settings(environment="development")
    assert settings.is_production is False
    assert settings.demo_login_allowed is True
    assert settings.jwt_verification_mode == "hybrid"


def test_statement_upload_ceiling_cannot_exceed_provider_limit() -> None:
    with pytest.raises(ValidationError):
        Settings(statement_max_upload_bytes=15 * 1024 * 1024 + 1)
