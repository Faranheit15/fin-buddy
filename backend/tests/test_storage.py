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
