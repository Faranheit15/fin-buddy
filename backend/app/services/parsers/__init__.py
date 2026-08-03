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


__all__ = [
    "ParseResult",
    "ParsedLine",
    "StatementParser",
    "parse_statement_text",
    "select_parser",
]
