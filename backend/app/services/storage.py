"""Statement file storage — local filesystem or private Supabase Storage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal
from urllib.parse import urljoin
from uuid import UUID

import httpx

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.core.security import is_opaque_supabase_key

logger = get_logger(__name__)

StorageBackend = Literal["local", "supabase"]


@dataclass(frozen=True, slots=True)
class StorageObjectMetadata:
    size_bytes: int
    content_type: str | None


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


def statement_relative_path(
    organization_id: UUID,
    statement_id: UUID,
    ext: str,
    user_id: UUID | None = None,
) -> str:
    """Build a server-owned path; the optional user segment is used for new uploads."""
    safe_ext = ext.lstrip(".").lower() or "bin"
    if user_id is None:
        return f"{organization_id}/{statement_id}.{safe_ext}"
    return f"{organization_id}/{user_id}/{statement_id}.{safe_ext}"


def absolute_path(relative: str, settings: Settings | None = None) -> Path:
    return storage_root(settings) / _safe_relative_path(relative)


def _safe_relative_path(relative: str) -> str:
    clean = relative.strip("/")
    path = PurePosixPath(clean)
    if (
        not clean
        or clean != relative
        or path.is_absolute()
        or "\\" in relative
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise AppError(
            "Invalid statement storage path", code="invalid_storage_path", status_code=500
        )
    return str(path)


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
    if lower.endswith(".xlsx"):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "application/octet-stream"


def _supabase_object_url(settings: Settings, relative: str) -> str:
    if not settings.supabase_url:
        raise AppError(
            "Statement storage is not configured", code="storage_not_configured", status_code=503
        )
    bucket = settings.statement_storage_bucket.strip("/")
    if not bucket or "/" in bucket:
        raise AppError(
            "Statement storage is not configured", code="storage_not_configured", status_code=503
        )
    base = settings.supabase_url.rstrip("/")
    object_path = _safe_relative_path(relative)
    return f"{base}/storage/v1/object/{bucket}/{object_path}"


def _supabase_headers(settings: Settings) -> dict[str, str]:
    key = settings.supabase_service_role_key
    if not key:
        raise AppError(
            "Statement storage is not configured", code="storage_not_configured", status_code=503
        )
    headers = {"apikey": key}
    if not is_opaque_supabase_key(key):
        headers["Authorization"] = f"Bearer {key}"
    return headers


async def create_signed_upload_url(
    relative: str,
    settings: Settings | None = None,
) -> str:
    """Issue a Supabase upload URL; the service-role key never leaves this process."""
    cfg = settings or get_settings()
    if storage_backend(cfg) != "supabase":
        raise AppError(
            "Direct statement uploads require Supabase Storage",
            code="storage_not_configured",
            status_code=503,
        )
    object_url = _supabase_object_url(cfg, relative)
    sign_url = object_url.replace("/object/", "/object/upload/sign/", 1)
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        response = await client.post(sign_url, headers=_supabase_headers(cfg), json={})
    if response.status_code >= 400:
        logger.error("supabase_storage_sign_failed", status=response.status_code, path=relative)
        raise AppError(
            "Could not prepare statement upload", code="storage_sign_failed", status_code=502
        )
    try:
        payload = response.json()
        signed_path = payload.get("url")
    except ValueError as exc:
        raise AppError(
            "Could not prepare statement upload", code="storage_sign_failed", status_code=502
        ) from exc
    if not isinstance(signed_path, str) or "token=" not in signed_path:
        raise AppError(
            "Could not prepare statement upload", code="storage_sign_failed", status_code=502
        )
    base = cfg.supabase_url.rstrip("/") if cfg.supabase_url else ""
    if signed_path.startswith("http"):
        return signed_path
    normalized_path = signed_path.lstrip("/")
    if not normalized_path.startswith("storage/v1/"):
        normalized_path = f"storage/v1/{normalized_path}"
    return urljoin(f"{base}/", normalized_path)


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


async def object_metadata(relative: str, settings: Settings | None = None) -> StorageObjectMetadata:
    cfg = settings or get_settings()
    if storage_backend(cfg) == "local":
        path = absolute_path(relative, cfg)
        if not path.is_file():
            raise FileNotFoundError(relative)
        return StorageObjectMetadata(path.stat().st_size, _content_type_for(relative))

    url = _supabase_object_url(cfg, relative)
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        response = await client.head(url, headers=_supabase_headers(cfg))
        if response.status_code == 404:
            raise FileNotFoundError(relative)
        # Some Supabase/edge responses omit Content-Length for HEAD. Probe one
        # byte so Content-Range can provide the authoritative total without
        # downloading the object into memory.
        head_size = _content_length(response)
        if response.status_code in {405, 501} or not head_size:
            response = await client.get(
                url, headers={**_supabase_headers(cfg), "Range": "bytes=0-0"}
            )
    if response.status_code == 404:
        raise FileNotFoundError(relative)
    if response.status_code >= 400:
        raise AppError(
            "Failed to inspect statement file", code="storage_metadata_failed", status_code=502
        )
    content_range = response.headers.get("content-range", "")
    size: int | None
    if content_range:
        try:
            # A one-byte range response reports Content-Length: 1. The total
            # object size is the value after the slash in Content-Range.
            size = int(content_range.rsplit("/", 1)[1])
        except (IndexError, ValueError):
            raise AppError(
                "Failed to inspect statement file", code="storage_metadata_failed", status_code=502
            ) from None
    else:
        size = _content_length(response)
    if size is None:
        raise AppError(
            "Failed to inspect statement file", code="storage_metadata_failed", status_code=502
        )
    content_type = response.headers.get("content-type")
    logger.info(
        "supabase_storage_metadata",
        size_bytes=size,
        content_type=content_type,
    )
    return StorageObjectMetadata(size, content_type)


async def read_bytes(
    relative: str,
    settings: Settings | None = None,
    *,
    max_bytes: int | None = None,
) -> bytes:
    cfg = settings or get_settings()
    limit = max_bytes or 15 * 1024 * 1024
    if storage_backend(cfg) == "local":
        path = absolute_path(relative, cfg)
        if not path.is_file():
            raise FileNotFoundError(relative)
        if path.stat().st_size > limit:
            raise AppError(
                "Statement file exceeds the configured limit",
                code="upload_too_large",
                status_code=413,
            )
        return path.read_bytes()

    url = _supabase_object_url(cfg, relative)
    chunks: list[bytes] = []
    total = 0
    async with (
        httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client,
        client.stream("GET", url, headers=_supabase_headers(cfg)) as response,
    ):
        if response.status_code == 404:
            raise FileNotFoundError(relative)
        if response.status_code >= 400:
            raise AppError(
                "Failed to read statement file", code="storage_download_failed", status_code=502
            )
        declared_size = _content_length(response)
        if declared_size is not None and declared_size > limit:
            raise AppError(
                "Statement file exceeds the configured limit",
                code="upload_too_large",
                status_code=413,
            )
        async for chunk in response.aiter_bytes(1024 * 1024):
            total += len(chunk)
            if total > limit:
                raise AppError(
                    "Statement file exceeds the configured limit",
                    code="upload_too_large",
                    status_code=413,
                )
            chunks.append(chunk)
    return b"".join(chunks)


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


def _content_length(response: httpx.Response) -> int | None:
    value = response.headers.get("content-length")
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


async def _supabase_upload(relative: str, data: bytes, settings: Settings) -> None:
    url = _supabase_object_url(settings, relative)
    headers = {
        **_supabase_headers(settings),
        "Content-Type": _content_type_for(relative),
        "x-upsert": "false",
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        response = await client.post(url, headers=headers, content=data)
    if response.status_code >= 400:
        logger.error("supabase_storage_upload_failed", status=response.status_code, path=relative)
        raise AppError(
            "Failed to store statement file", code="storage_upload_failed", status_code=502
        )


async def _supabase_delete(relative: str, settings: Settings) -> None:
    url = _supabase_object_url(settings, relative)
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        response = await client.delete(url, headers=_supabase_headers(settings))
    if response.status_code in (404, 400):
        return
    if response.status_code >= 400:
        logger.warning("supabase_storage_delete_failed", status=response.status_code, path=relative)
        raise AppError(
            "Failed to clean up statement file", code="storage_delete_failed", status_code=502
        )
