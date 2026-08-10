"""Bounded streaming helpers and early guards for user-provided uploads."""

from __future__ import annotations

from typing import Protocol

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.exceptions import AppError

READ_CHUNK_BYTES = 1024 * 1024
STATEMENT_UPLOAD_PATH = "/api/v1/statements/upload"
# Multipart boundaries and form fields add a small amount beyond the file-size limit.
MULTIPART_OVERHEAD_BYTES = 64 * 1024


class AsyncUploadReader(Protocol):
    async def read(self, size: int = -1) -> bytes: ...


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
