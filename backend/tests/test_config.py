"""Settings helpers."""

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
