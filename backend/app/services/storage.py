"""Statement file storage — local filesystem or Supabase Storage."""

from __future__ import annotations

from pathlib import Path
from typing import Literal
from uuid import UUID

import httpx

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.core.security import is_opaque_supabase_key

logger = get_logger(__name__)

StorageBackend = Literal["local", "supabase"]


def storage_backend(settings: Settings | None = None) -> StorageBackend:
    cfg = settings or get_settings()
    backend = (cfg.statement_storage_backend or "local").lower().strip()
    if backend == "supabase":
        return "supabase"
    return "local"


def storage_root(settings: Settings | None = None) -> Path:
    cfg = settings or get_settings()
    root = Path(cfg.statement_storage_dir)
    if not root.is_absolute():
        backend_root = Path(__file__).resolve().parents[2]
        root = backend_root / root
    root.mkdir(parents=True, exist_ok=True)
    return root


def statement_relative_path(organization_id: UUID, statement_id: UUID, ext: str) -> str:
    safe_ext = ext.lstrip(".").lower() or "bin"
    return f"{organization_id}/{statement_id}.{safe_ext}"


def absolute_path(relative: str, settings: Settings | None = None) -> Path:
    return storage_root(settings) / relative


def _content_type_for(relative: str) -> str:
    lower = relative.lower()
    if lower.endswith(".pdf"):
        return "application/pdf"
    if lower.endswith(".csv"):
        return "text/csv"
    if lower.endswith(".tsv"):
        return "text/tab-separated-values"
    if lower.endswith(".txt"):
        return "text/plain"
    return "application/octet-stream"


def _supabase_object_url(settings: Settings, relative: str) -> str:
    if not settings.supabase_url:
        raise AppError(
            "SUPABASE_URL is required for statement storage",
            code="storage_not_configured",
            status_code=503,
        )
    bucket = settings.statement_storage_bucket.strip("/")
    base = settings.supabase_url.rstrip("/")
    object_path = relative.lstrip("/")
    return f"{base}/storage/v1/object/{bucket}/{object_path}"


def _supabase_headers(settings: Settings) -> dict[str, str]:
    key = settings.supabase_service_role_key
    if not key:
        raise AppError(
            "SUPABASE_SERVICE_ROLE_KEY is required for statement storage",
            code="storage_not_configured",
            status_code=503,
        )
    headers = {"apikey": key}
    if not is_opaque_supabase_key(key):
        headers["Authorization"] = f"Bearer {key}"
    return headers


async def save_bytes(
    relative: str,
    data: bytes,
    settings: Settings | None = None,
) -> str:
    cfg = settings or get_settings()
    if storage_backend(cfg) == "supabase":
        await _supabase_upload(relative, data, cfg)
        return relative
    path = absolute_path(relative, cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return relative


async def read_bytes(relative: str, settings: Settings | None = None) -> bytes:
    cfg = settings or get_settings()
    if storage_backend(cfg) == "supabase":
        return await _supabase_download(relative, cfg)
    path = absolute_path(relative, cfg)
    if not path.is_file():
        raise FileNotFoundError(relative)
    return path.read_bytes()


async def delete_file(relative: str | None, settings: Settings | None = None) -> None:
    if not relative:
        return
    cfg = settings or get_settings()
    if storage_backend(cfg) == "supabase":
        await _supabase_delete(relative, cfg)
        return
    path = absolute_path(relative, cfg)
    if path.is_file():
        path.unlink()


async def _supabase_upload(relative: str, data: bytes, settings: Settings) -> None:
    url = _supabase_object_url(settings, relative)
    headers = {
        **_supabase_headers(settings),
        "Content-Type": _content_type_for(relative),
        "x-upsert": "true",
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        response = await client.post(url, headers=headers, content=data)
        if response.status_code >= 400:
            logger.error(
                "supabase_storage_upload_failed",
                status=response.status_code,
                body=response.text[:500],
                path=relative,
            )
            raise AppError(
                "Failed to store statement file",
                code="storage_upload_failed",
                status_code=502,
                details={"status": response.status_code},
            )


async def _supabase_download(relative: str, settings: Settings) -> bytes:
    url = _supabase_object_url(settings, relative)
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        response = await client.get(url, headers=_supabase_headers(settings))
        if response.status_code == 404:
            raise FileNotFoundError(relative)
        if response.status_code >= 400:
            logger.error(
                "supabase_storage_download_failed",
                status=response.status_code,
                body=response.text[:500],
                path=relative,
            )
            raise AppError(
                "Failed to read statement file",
                code="storage_download_failed",
                status_code=502,
            )
        return response.content


async def _supabase_delete(relative: str, settings: Settings) -> None:
    url = _supabase_object_url(settings, relative)
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        response = await client.delete(url, headers=_supabase_headers(settings))
        if response.status_code in (404, 400):
            return
        if response.status_code >= 400:
            logger.warning(
                "supabase_storage_delete_failed",
                status=response.status_code,
                path=relative,
            )
