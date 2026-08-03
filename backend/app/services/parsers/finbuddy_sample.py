"""Structured FinBuddy sample statement format (reliable demos + tests).

Example body::

    FINBUDDY_STATEMENT
    CARD:4821
    PERIOD:2026-06-15..2026-07-14
    STATEMENT_DATE:2026-07-15
    DUE_DATE:2026-08-04
    ---
    2026-07-01|purchase|SWIGGY BANGALORE|2450.00
    2026-07-05|purchase|AMAZON PAY|1299.00
    2026-07-10|refund|AMAZON PAY|500.00
    2026-07-12|payment_to_issuer|PAYMENT THANK YOU|15000.00
"""

from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.models.enums import TransactionType
from app.services.parsers.base import ParsedLine, ParseResult

IST = ZoneInfo("Asia/Kolkata")

_HEADER = "FINBUDDY_STATEMENT"

_TYPE_MAP = {
    "purchase": TransactionType.PURCHASE,
    "refund": TransactionType.REFUND,
    "fee": TransactionType.FEE,
    "interest": TransactionType.INTEREST,
    "payment_to_issuer": TransactionType.PAYMENT_TO_ISSUER,
    "payment": TransactionType.PAYMENT_TO_ISSUER,
    "opening_balance": TransactionType.OPENING_BALANCE,
}


def _rupees_to_paise(value: str) -> int:
    cleaned = value.replace(",", "").replace("₹", "").strip()
    if not cleaned:
        return 0
    # Allow leading minus; amount stored absolute
    amount = abs(float(cleaned))
    return int(round(amount * 100))


def _parse_date(value: str) -> date:
    return date.fromisoformat(value.strip())


class FinBuddySampleParser:
    name = "finbuddy_sample"

    def can_parse(self, text: str, *, issuer: str | None = None) -> bool:
        return _HEADER in text.upper() or text.lstrip().upper().startswith(_HEADER)

    def parse(self, text: str, *, issuer: str | None = None) -> ParseResult:
        lines_out: list[ParsedLine] = []
        period_start: date | None = None
        period_end: date | None = None
        statement_date: date | None = None
        due_date: date | None = None
        in_body = False

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            upper = line.upper()
            if upper == _HEADER or upper.startswith(_HEADER):
                continue
            if line == "---":
                in_body = True
                continue
            if not in_body and ":" in line and "|" not in line:
                key, _, val = line.partition(":")
                key_u = key.strip().upper()
                val = val.strip()
                if key_u == "PERIOD" and ".." in val:
                    left, _, right = val.partition("..")
                    period_start = _parse_date(left)
                    period_end = _parse_date(right)
                elif key_u == "STATEMENT_DATE":
                    statement_date = _parse_date(val)
                elif key_u == "DUE_DATE":
                    due_date = _parse_date(val)
                continue

            # Body rows: date|type|merchant|amount
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 4:
                # Also allow tab-separated
                parts = [p.strip() for p in line.split("\t")]
            if len(parts) < 4:
                continue

            day = _parse_date(parts[0])
            type_key = parts[1].lower().replace(" ", "_")
            proposed = _TYPE_MAP.get(type_key, TransactionType.PURCHASE)
            merchant = parts[2][:255] or "Unknown"
            amount_paise = _rupees_to_paise(parts[3])
            if amount_paise <= 0:
                continue

            occurred = datetime.combine(day, time(12, 0), tzinfo=IST)
            lines_out.append(
                ParsedLine(
                    occurred_at=occurred,
                    merchant=merchant,
                    amount_paise=amount_paise,
                    proposed_type=proposed,
                    raw={"source": "finbuddy_sample", "line": raw_line},
                )
            )

        return ParseResult(
            lines=lines_out,
            parser_name=self.name,
            period_start=period_start,
            period_end=period_end,
            statement_date=statement_date,
            due_date=due_date,
            notes=f"Parsed {len(lines_out)} lines via FinBuddy sample format",
        )
