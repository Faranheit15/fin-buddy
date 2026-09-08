"""Regression tests for bounded upload reads and statement content guards."""

import io
import zipfile

import pytest

from app.core.exceptions import AppError
from app.core.upload_limits import (
    read_upload_limited,
    statement_file_spec,
    validate_statement_bytes,
)


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


@pytest.mark.parametrize(
    ("filename", "content_type"),
    [
        ("statement.pdf", "text/plain"),
        ("statement.exe", "application/octet-stream"),
        ("../statement.txt", "text/plain"),
    ],
)
def test_statement_metadata_rejects_wrong_type_or_path(filename: str, content_type: str) -> None:
    with pytest.raises(AppError):
        statement_file_spec(filename, content_type, 10, max_bytes=100)


def test_statement_content_guards_check_signatures_and_utf8() -> None:
    assert (
        validate_statement_bytes(
            b"%PDF-1.7\n", "statement.pdf", "application/pdf", max_bytes=100
        ).extension
        == "pdf"
    )
    with pytest.raises(AppError, match="valid PDF"):
        validate_statement_bytes(b"not a pdf", "statement.pdf", "application/pdf", max_bytes=100)
    with pytest.raises(AppError, match="UTF-8"):
        validate_statement_bytes(b"\xff", "statement.txt", "text/plain", max_bytes=100)


def test_xlsx_guard_rejects_malformed_and_decompression_bomb() -> None:
    with pytest.raises(AppError, match="malformed"):
        validate_statement_bytes(
            b"not a zip",
            "statement.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            max_bytes=100,
        )

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("xl/workbook.xml", "x" * 20)
    with pytest.raises(AppError, match="resource limit"):
        validate_statement_bytes(
            archive.getvalue(),
            "statement.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            max_bytes=10_000,
            max_decompressed_bytes=10,
        )
