"""Statement parsers registry."""

from __future__ import annotations

from app.core.upload_config import (
    PARSER_MAX_COLUMNS,
    PARSER_MAX_DECOMPRESSED_BYTES,
    PARSER_MAX_LINES,
    PARSER_MAX_PDF_PAGES,
    PARSER_MAX_ROWS,
    PARSER_MAX_SHEETS,
    PARSER_MAX_TEXT_CHARS,
)
from app.services.parsers.base import ParsedLine, ParseResult, StatementParser
from app.services.parsers.finbuddy_sample import FinBuddySampleParser
from app.services.parsers.generic import GenericTextParser

_PARSERS: list[StatementParser] = [
    FinBuddySampleParser(),
    GenericTextParser(),
]


def select_parser(text: str, *, issuer: str | None = None) -> StatementParser:
    for parser in _PARSERS:
        if parser.can_parse(text, issuer=issuer):
            return parser
    return GenericTextParser()


def parse_statement_text(text: str, *, issuer: str | None = None) -> ParseResult:
    parser = select_parser(text, issuer=issuer)
    return parser.parse(text, issuer=issuer)


def parse_statement_bytes(
    data: bytes,
    filename: str,
    *,
    issuer: str | None = None,
    max_rows: int = PARSER_MAX_ROWS,
    max_columns: int = PARSER_MAX_COLUMNS,
    max_sheets: int = PARSER_MAX_SHEETS,
    max_pdf_pages: int = PARSER_MAX_PDF_PAGES,
    max_decompressed_bytes: int = PARSER_MAX_DECOMPRESSED_BYTES,
    max_lines: int = PARSER_MAX_LINES,
    max_text_chars: int = PARSER_MAX_TEXT_CHARS,
) -> ParseResult:
    lower = filename.lower()
    if lower.endswith((".csv", ".tsv", ".xlsx")):
        from app.services.parsers.csv_excel import CsvExcelParser

        return CsvExcelParser().parse_bytes(
            data,
            filename,
            issuer=issuer,
            max_rows=max_rows,
            max_columns=max_columns,
            max_sheets=max_sheets,
            max_lines=max_lines,
        )

    from app.services.statement_service import extract_text_from_bytes

    text = extract_text_from_bytes(
        data,
        filename,
        max_pdf_pages=max_pdf_pages,
        max_text_chars=max_text_chars,
    )
    result = parse_statement_text(text, issuer=issuer)
    if len(result.lines) > max_lines:
        from app.core.exceptions import AppError

        raise AppError("The statement exceeds the parser line limit", code="parser_resource_limit")
    return result


__all__ = [
    "ParseResult",
    "ParsedLine",
    "StatementParser",
    "parse_statement_text",
    "parse_statement_bytes",
    "select_parser",
]
