"""Local statement storage backend tests."""

from pathlib import Path
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.services import storage


@pytest.mark.asyncio
async def test_local_save_read_delete(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STATEMENT_STORAGE_BACKEND", "local")
    monkeypatch.setenv("STATEMENT_STORAGE_DIR", str(tmp_path))
    from app.core.config import get_settings

    get_settings.cache_clear()
    settings = Settings(
        statement_storage_backend="local",
        statement_storage_dir=str(tmp_path),
    )

    relative = storage.statement_relative_path(uuid4(), uuid4(), "txt")
    payload = b"FINBUDDY_STATEMENT\n"
    await storage.save_bytes(relative, payload, settings)
    assert await storage.read_bytes(relative, settings) == payload
    await storage.delete_file(relative, settings)
    with pytest.raises(FileNotFoundError):
        await storage.read_bytes(relative, settings)
    get_settings.cache_clear()


def test_statement_relative_path_shape() -> None:
    org = uuid4()
    stmt = uuid4()
    path = storage.statement_relative_path(org, stmt, "pdf")
    assert path == f"{org}/{stmt}.pdf"


def test_supabase_headers_opaque_secret_key() -> None:
    settings = Settings(
        supabase_url="https://test.supabase.co",
        supabase_service_role_key="sb_secret_abcdef1234567890",
    )
    headers = storage._supabase_headers(settings)
    assert headers["apikey"] == "sb_secret_abcdef1234567890"
    # Opaque keys must NEVER be sent as Authorization: Bearer
    assert "Authorization" not in headers


def test_supabase_headers_legacy_jwt_key() -> None:
    legacy_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIn0.fake_signature"
    settings = Settings(
        supabase_url="https://test.supabase.co",
        supabase_service_role_key=legacy_jwt,
    )
    headers = storage._supabase_headers(settings)
    assert headers["apikey"] == legacy_jwt
    assert headers["Authorization"] == f"Bearer {legacy_jwt}"
