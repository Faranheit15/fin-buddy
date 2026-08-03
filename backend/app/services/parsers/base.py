"""Pluggable statement parser interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Protocol

from app.models.enums import TransactionType


@dataclass(slots=True)
class ParsedLine:
    occurred_at: datetime | None
    merchant: str
    amount_paise: int
    proposed_type: TransactionType
    raw: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class ParseResult:
    lines: list[ParsedLine]
    parser_name: str
    period_start: date | None = None
    period_end: date | None = None
    statement_date: date | None = None
    due_date: date | None = None
    notes: str | None = None


class StatementParser(Protocol):
    name: str

    def can_parse(self, text: str, *, issuer: str | None = None) -> bool:
        """Return True if this parser should handle the extracted text."""
        ...

    def parse(self, text: str, *, issuer: str | None = None) -> ParseResult:
        """Parse statement text into candidate lines + optional metadata."""
        ...
