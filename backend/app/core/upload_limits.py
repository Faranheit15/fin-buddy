"""Bounded upload helpers and content guards for user-provided statements."""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from pathlib import PurePath
from typing import Protocol

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.exceptions import AppError
from app.core.upload_config import (
    PARSER_MAX_DECOMPRESSED_BYTES,
)

READ_CHUNK_BYTES = 1024 * 1024
STATEMENT_UPLOAD_PATH = "/api/v1/statements/upload"
# Multipart boundaries and form fields add a small amount beyond the file-size limit.
MULTIPART_OVERHEAD_BYTES = 64 * 1024


@dataclass(frozen=True, slots=True)
class StatementFileSpec:
    extension: str
    content_type: str


_STATEMENT_SPECS = {
    ".pdf": StatementFileSpec("pdf", "application/pdf"),
    ".txt": StatementFileSpec("txt", "text/plain"),
    ".csv": StatementFileSpec("csv", "text/csv"),
    ".tsv": StatementFileSpec("tsv", "text/tab-separated-values"),
    ".xlsx": StatementFileSpec(
        "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ),
}


class AsyncUploadReader(Protocol):
    async def read(self, size: int = -1) -> bytes: ...


def statement_file_spec(
    filename: str, content_type: str, size_bytes: int, *, max_bytes: int
) -> StatementFileSpec:
    """Validate client metadata before issuing a Storage upload URL."""
    clean_name = (filename or "").strip()
    if (
        not clean_name
        or len(clean_name) > 255
        or clean_name != PurePath(clean_name).name
        or "\\" in clean_name
        or "\x00" in clean_name
    ):
        raise AppError("Choose a statement file with a valid name", code="invalid_file_name")

    spec = _STATEMENT_SPECS.get(PurePath(clean_name.lower()).suffix)
    if spec is None:
        raise AppError(
            "Unsupported statement file type. Use PDF, CSV, TSV, XLSX, or TXT.",
            code="unsupported_file_type",
            status_code=415,
        )
    if size_bytes <= 0:
        raise AppError("Statement file is empty", code="empty_upload")
    if size_bytes > max_bytes:
        raise AppError(
            f"Statement file is too large (maximum {max_bytes // (1024 * 1024)} MB)",
            code="upload_too_large",
            status_code=413,
        )

    normalized_type = (content_type or "").split(";", 1)[0].strip().lower()
    if normalized_type != spec.content_type:
        raise AppError(
            f"The selected file must be uploaded as {spec.content_type}",
            code="invalid_file_type",
            status_code=415,
        )
    return spec


def validate_statement_bytes(
    data: bytes,
    filename: str,
    content_type: str,
    *,
    max_bytes: int,
    max_decompressed_bytes: int = PARSER_MAX_DECOMPRESSED_BYTES,
) -> StatementFileSpec:
    """Validate size, declared type, and a cheap content signature before parsing."""
    spec = statement_file_spec(filename, content_type, len(data), max_bytes=max_bytes)
    if spec.extension == "pdf" and not data.startswith(b"%PDF"):
        raise AppError("The file is not a valid PDF", code="invalid_file_content", status_code=415)
    if spec.extension in {"txt", "csv", "tsv"}:
        if b"\x00" in data:
            raise AppError(
                "The text statement contains invalid binary content",
                code="invalid_file_content",
                status_code=415,
            )
        try:
            data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise AppError(
                "The text statement must be UTF-8 encoded",
                code="invalid_file_content",
                status_code=415,
            ) from exc
    if spec.extension == "xlsx":
        _validate_xlsx_archive(data, max_decompressed_bytes=max_decompressed_bytes)
    return spec


def _validate_xlsx_archive(data: bytes, *, max_decompressed_bytes: int) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = archive.infolist()
            if len(members) > 4_000:
                raise AppError(
                    "The spreadsheet contains too many internal parts",
                    code="parser_resource_limit",
                )
            if any(member.flag_bits & 0x1 for member in members):
                raise AppError(
                    "Encrypted spreadsheets are not supported", code="invalid_file_content"
                )
            uncompressed_bytes = sum(member.file_size for member in members)
            if uncompressed_bytes > max_decompressed_bytes:
                raise AppError(
                    "The spreadsheet exceeds the parser resource limit",
                    code="parser_resource_limit",
                )
            if "xl/workbook.xml" not in archive.namelist():
                raise AppError("The file is not a valid XLSX workbook", code="invalid_file_content")
    except AppError:
        raise
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise AppError(
            "The spreadsheet is malformed or unreadable", code="invalid_file_content"
        ) from exc


async def read_upload_limited(
    upload: AsyncUploadReader,
    *,
    max_bytes: int,
    chunk_bytes: int = READ_CHUNK_BYTES,
) -> bytes:
    """Read an upload in bounded chunks and reject it immediately above the limit."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(chunk_bytes)
        if not chunk:
            return b"".join(chunks)
        total += len(chunk)
        if total > max_bytes:
            raise AppError(
                f"File too large (max {max_bytes // (1024 * 1024)} MB)",
                code="upload_too_large",
                status_code=413,
            )
        chunks.append(chunk)


class StatementUploadLimitMiddleware(BaseHTTPMiddleware):
    """Reject known oversized statement requests before multipart parsing allocates resources."""

    def __init__(self, app: ASGIApp, *, max_upload_bytes: int) -> None:
        super().__init__(app)
        self._max_request_bytes = max_upload_bytes + MULTIPART_OVERHEAD_BYTES

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "POST" and request.url.path == STATEMENT_UPLOAD_PATH:
            raw_length = request.headers.get("content-length")
            if raw_length:
                try:
                    content_length = int(raw_length)
                except ValueError:
                    content_length = 0
                if content_length > self._max_request_bytes:
                    return JSONResponse(
                        {
                            "error": {
                                "code": "upload_too_large",
                                "message": "Statement upload exceeds the configured limit",
                            }
                        },
                        status_code=413,
                    )
        return await call_next(request)
