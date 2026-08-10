"""Statement parsers registry."""

from __future__ import annotations

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


def parse_statement_bytes(data: bytes, filename: str, *, issuer: str | None = None) -> ParseResult:
    lower = filename.lower()
    if lower.endswith(".csv") or lower.endswith(".xlsx"):
        from app.services.parsers.csv_excel import CsvExcelParser

        return CsvExcelParser().parse_bytes(data, filename, issuer=issuer)

    from app.services.statement_service import extract_text_from_bytes

    text = extract_text_from_bytes(data, filename)
    return parse_statement_text(text, issuer=issuer)


__all__ = [
    "ParseResult",
    "ParsedLine",
    "StatementParser",
    "parse_statement_text",
    "parse_statement_bytes",
    "select_parser",
]
