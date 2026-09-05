"""Application settings loaded from environment variables."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Annotated, Literal
from urllib.parse import urlparse, urlunparse

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _parse_string_list(value: object) -> list[str]:
    """
    Accept comma-separated strings, JSON arrays, or real lists.

    pydantic-settings JSON-decodes list fields by default; NoDecode keeps the raw
    string so we can support simple .env values like:
      CORS_ORIGINS=http://localhost:3000
      CORS_ORIGINS=http://localhost:3000,https://app.example.com
    """
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("["):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        # Strip optional surrounding quotes from a single origin
        if (text.startswith('"') and text.endswith('"')) or (
            text.startswith("'") and text.endswith("'")
        ):
            text = text[1:-1].strip()
        return [item.strip() for item in text.split(",") if item.strip()]
    return [str(value).strip()] if str(value).strip() else []


class Settings(BaseSettings):
    """Runtime configuration for the Fin Buddy API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Fin Buddy API"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # CORS — comma-separated origins in .env (NoDecode: do not require JSON)
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)
    # Only these immediate peers may supply X-Forwarded-For. Keep empty unless
    # the deployment has a known reverse proxy in front of the API.
    trusted_proxy_ips: Annotated[list[str], NoDecode] = Field(default_factory=list)

    # Database (Supabase Postgres connection string)
    # Example: postgresql://postgres.[project-ref]:[password]@aws-0-...pooler.supabase.com:6543/postgres
    database_url: str | None = None
    database_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30

    # Auto migrate + seed on startup
    auto_migrate: bool = True
    auto_seed: bool = True

    # Supabase Auth
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    # JWT secret from Project Settings → API → JWT Secret
    supabase_jwt_secret: str | None = None
    supabase_jwt_audience: str = "authenticated"
    supabase_jwt_issuer: str | None = None  # defaults to {supabase_url}/auth/v1

    # Public frontend origin — used for email confirmation / magic-link redirects
    # Example: https://fin-buddy-dev.vercel.app
    frontend_app_url: str | None = None

    # Platform bootstrap: emails granted super_admin on seed/login (comma-separated)
    platform_admin_emails: Annotated[list[str], NoDecode] = Field(default_factory=list)

    # Demo login (no Supabase email) — disabled automatically in production unless forced
    demo_auth_enabled: bool | None = None
    demo_user_email: str = "demo@finbuddy.local"
    demo_user_name: str = "Demo User"

    # Statement PDF / text storage
    # local = filesystem under statement_storage_dir (dev / docker volume)
    # supabase = private bucket via Storage API (required for FastAPI Cloud)
    statement_storage_backend: Literal["local", "supabase"] = "local"
    statement_storage_dir: str = "storage/statements"
    statement_storage_bucket: str = "statements"
    statement_max_upload_bytes: int = 15 * 1024 * 1024  # 15 MB

    # Email provider (Resend)
    resend_api_key: str | None = None
    # Request / activity logging
    log_api_requests: bool = True
    log_request_body: bool = False  # avoid PII in prod unless needed
    operational_log_retention_days: int = Field(default=90, ge=1, le=3650)

    # Required by the externally scheduled reminder endpoint. Never expose it
    # to browsers; a scheduler sends it in X-Job-Secret.
    job_runner_secret: str | None = None

    @field_validator("cors_origins", "platform_admin_emails", "trusted_proxy_ips", mode="before")
    @classmethod
    def parse_csv_list(cls, value: object) -> list[str]:
        return _parse_string_list(value)

    @model_validator(mode="after")
    def derive_jwt_issuer(self) -> Settings:
        if self.supabase_jwt_issuer is None and self.supabase_url:
            object.__setattr__(
                self,
                "supabase_jwt_issuer",
                f"{self.supabase_url.rstrip('/')}/auth/v1",
            )
        return self

    @model_validator(mode="after")
    def validate_production_invariants(self) -> Settings:
        if self.is_production:
            if self.debug:
                raise ValueError("Production mode requires DEBUG=false")
            if self.demo_auth_enabled is True:
                raise ValueError("Production mode requires DEMO_AUTH_ENABLED=false")
            if self.auto_migrate:
                raise ValueError(
                    "Production mode requires AUTO_MIGRATE=false (run migrations via explicit release gate)"
                )
            if self.auto_seed:
                raise ValueError("Production mode requires AUTO_SEED=false")
            if self.statement_storage_backend != "supabase":
                raise ValueError("Production mode requires STATEMENT_STORAGE_BACKEND=supabase")
            if not self.statement_storage_bucket:
                raise ValueError("Production mode requires STATEMENT_STORAGE_BUCKET to be configured")
            if not self.database_url:
                raise ValueError("Production mode requires DATABASE_URL to be set")
            if not self.supabase_url:
                raise ValueError("Production mode requires SUPABASE_URL to be set")
            if not self.supabase_service_role_key:
                raise ValueError("Production mode requires SUPABASE_SERVICE_ROLE_KEY to be set")
            if not self.supabase_jwt_secret:
                raise ValueError("Production mode requires SUPABASE_JWT_SECRET to be set")
            if (
                self.supabase_jwt_secret == "fin-buddy-demo-dev-secret-change-me"
                or len(self.supabase_jwt_secret.strip()) < 16
            ):
                raise ValueError("Production mode requires a strong, non-default SUPABASE_JWT_SECRET")
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_test(self) -> bool:
        return self.environment == "test"

    @property
    def auth_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_jwt_secret and self.supabase_anon_key)

    @property
    def demo_login_allowed(self) -> bool:
        """Demo auth: on in development/test by default; strictly disabled in production."""
        if self.is_production:
            return False
        return self.demo_auth_enabled is not False

    @property
    def database_configured(self) -> bool:
        return bool(self.database_url)

    def async_database_url(self) -> str:
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is not configured")
        return _with_driver(self.database_url, "postgresql+asyncpg")

    def sync_database_url(self) -> str:
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is not configured")
        return _with_driver(self.database_url, "postgresql+psycopg")


def _with_driver(url: str, driver: str) -> str:
    """Normalize a postgres URL to the requested SQLAlchemy driver."""
    # Handle already-qualified URLs
    if url.startswith("postgresql+"):
        scheme_end = url.index("://")
        rest = url[scheme_end:]
        return f"{driver}{rest}"
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return driver + url[len("postgresql") :]
    # Fallback: parse
    parsed = urlparse(url)
    return urlunparse(parsed._replace(scheme=driver.replace("+", ".")))


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
