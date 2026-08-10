"""Regression tests for bounded upload reads."""

import pytest

from app.core.exceptions import AppError
from app.core.upload_limits import read_upload_limited


class _ChunkedUpload:
    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = chunks
        self.reads = 0

    async def read(self, _size: int = -1) -> bytes:
        self.reads += 1
        return self._chunks.pop(0) if self._chunks else b""


@pytest.mark.asyncio
async def test_upload_read_stops_once_limit_is_exceeded() -> None:
    upload = _ChunkedUpload([b"abcd", b"efgh", b"unread"])

    with pytest.raises(AppError, match="File too large") as exc_info:
        await read_upload_limited(upload, max_bytes=6, chunk_bytes=4)

    assert exc_info.value.status_code == 413
    assert upload.reads == 2


@pytest.mark.asyncio
async def test_upload_read_returns_small_payload() -> None:
    upload = _ChunkedUpload([b"abcd", b"ef", b""])

    assert await read_upload_limited(upload, max_bytes=6, chunk_bytes=4) == b"abcdef"
