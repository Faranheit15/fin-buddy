"""Local filesystem storage for statement uploads (v1)."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from app.core.config import Settings, get_settings


def storage_root(settings: Settings | None = None) -> Path:
    cfg = settings or get_settings()
    root = Path(cfg.statement_storage_dir)
    if not root.is_absolute():
        # Resolve relative to backend package parent (backend/)
        backend_root = Path(__file__).resolve().parents[2]
        root = backend_root / root
    root.mkdir(parents=True, exist_ok=True)
    return root


def statement_relative_path(organization_id: UUID, statement_id: UUID, ext: str) -> str:
    safe_ext = ext.lstrip(".").lower() or "bin"
    return f"{organization_id}/{statement_id}.{safe_ext}"


def absolute_path(relative: str, settings: Settings | None = None) -> Path:
    return storage_root(settings) / relative


def save_bytes(
    relative: str,
    data: bytes,
    settings: Settings | None = None,
) -> Path:
    path = absolute_path(relative, settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def read_bytes(relative: str, settings: Settings | None = None) -> bytes:
    path = absolute_path(relative, settings)
    if not path.is_file():
        raise FileNotFoundError(relative)
    return path.read_bytes()


def delete_file(relative: str | None, settings: Settings | None = None) -> None:
    if not relative:
        return
    path = absolute_path(relative, settings)
    if path.is_file():
        path.unlink()
