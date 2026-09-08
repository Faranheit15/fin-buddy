"""Local statement storage backend tests."""

from pathlib import Path
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.exceptions import AppError
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


def test_statement_relative_path_is_user_scoped() -> None:
    org = uuid4()
    user = uuid4()
    statement = uuid4()
    assert storage.statement_relative_path(org, statement, "xlsx", user) == (
        f"{org}/{user}/{statement}.xlsx"
    )


@pytest.mark.parametrize("path", ["../secret", "/absolute", "org\\user\\file.pdf", ""])
def test_storage_path_rejects_traversal(path: str) -> None:
    with pytest.raises(AppError, match="storage path"):
        storage._safe_relative_path(path)


@pytest.mark.asyncio
async def test_signed_upload_url_is_provider_url_without_service_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class _Response:
        status_code = 200

        def json(self) -> dict[str, str]:
            return {
                "url": "/object/upload/sign/statements/org/user/file.txt?token=opaque"
            }

    class _Client:
        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def post(
            self, url: str, *, headers: dict[str, str], json: dict[str, object]
        ) -> _Response:
            captured.update({"url": url, "headers": headers, "json": json})
            return _Response()

    monkeypatch.setattr(storage.httpx, "AsyncClient", lambda **_kwargs: _Client())
    settings = Settings(
        statement_storage_backend="supabase",
        supabase_url="https://test.supabase.co",
        statement_storage_bucket="statements",
        supabase_service_role_key="sb_secret_never_returned",
    )
    signed = await storage.create_signed_upload_url("org/user/file.txt", settings)

    assert signed.startswith("https://test.supabase.co/")
    assert "token=opaque" in signed
    assert "sb_secret" not in signed
    assert (
        captured["url"]
        == "https://test.supabase.co/storage/v1/object/upload/sign/statements/org/user/file.txt"
    )


@pytest.mark.asyncio
async def test_object_metadata_probes_range_when_head_has_no_size() -> None:
    class _Response:
        def __init__(self, status_code: int, headers: dict[str, str]) -> None:
            self.status_code = status_code
            self.headers = headers

    class _Client:
        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def head(self, *_args: object, **_kwargs: object) -> _Response:
            return _Response(200, {"content-length": "0", "content-type": "text/plain"})

        async def get(self, *_args: object, **kwargs: object) -> _Response:
            assert kwargs["headers"] == {
                "apikey": "sb_secret_test",
                "Range": "bytes=0-0",
            }
            return _Response(
                206,
                {
                    "content-length": "1",
                    "content-range": "bytes 0-0/322",
                    "content-type": "text/plain",
                },
            )

    original = storage.httpx.AsyncClient
    storage.httpx.AsyncClient = lambda **_kwargs: _Client()  # type: ignore[assignment]
    try:
        settings = Settings(
            statement_storage_backend="supabase",
            supabase_url="https://test.supabase.co",
            statement_storage_bucket="statements",
            supabase_service_role_key="sb_secret_test",
        )
        metadata = await storage.object_metadata("org/user/file.txt", settings)
    finally:
        storage.httpx.AsyncClient = original

    assert metadata.size_bytes == 322
    assert metadata.content_type == "text/plain"


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
    legacy_jwt = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIn0.fake_signature"
    )
    settings = Settings(
        supabase_url="https://test.supabase.co",
        supabase_service_role_key=legacy_jwt,
    )
    headers = storage._supabase_headers(settings)
    assert headers["apikey"] == legacy_jwt
    assert headers["Authorization"] == f"Bearer {legacy_jwt}"
