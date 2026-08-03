"""Generic statement text parser for loose bank PDF text extraction."""

from __future__ import annotations

import re
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.models.enums import TransactionType
from app.services.parsers.base import ParsedLine, ParseResult

IST = ZoneInfo("Asia/Kolkata")

# 01/07/2026 or 01-07-2026 or 2026-07-01
_DATE = r"(?P<date>(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(?:\d{4}-\d{2}-\d{2}))"
_AMOUNT = r"(?P<amount>[\d,]+(?:\.\d{1,2})?)"
_CRDR = r"(?P<crdr>CR|DR|Cr|Dr|CREDIT|DEBIT)?"

# Full line: date  merchant…  amount  [CR/DR]
_LINE_RE = re.compile(
    rf"^{_DATE}\s+(?P<merchant>.+?)\s+{_AMOUNT}\s*{_CRDR}\s*$",
    re.IGNORECASE,
)

# Amount-first fallbacks avoided — merchant ambiguity is high

_PAYMENT_HINTS = re.compile(
    r"\b(payment|paytm\s*bank|neft|imps|upi\s*payment|thank\s*you|auto.?debit)\b",
    re.I,
)
_REFUND_HINTS = re.compile(r"\b(refund|reversal|chargeback|cashback\s*credit)\b", re.I)
_FEE_HINTS = re.compile(r"\b(fee|gst|annual\s*fee|late\s*fee|finance\s*charge)\b", re.I)
_INTEREST_HINTS = re.compile(r"\b(interest|finance\s*charge)\b", re.I)


def _parse_date_token(token: str) -> date | None:
    token = token.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y"):
        try:
            return datetime.strptime(token, fmt).date()
        except ValueError:
            continue
    return None


def _rupees_to_paise(value: str) -> int:
    cleaned = value.replace(",", "").replace("₹", "").strip()
    if not cleaned:
        return 0
    return int(round(abs(float(cleaned)) * 100))


def _infer_type(merchant: str, crdr: str | None) -> TransactionType:
    m = merchant or ""
    flag = (crdr or "").upper()
    if _PAYMENT_HINTS.search(m) or flag in {"CR", "CREDIT"}:
        if _REFUND_HINTS.search(m):
            return TransactionType.REFUND
        if flag in {"CR", "CREDIT"} or _PAYMENT_HINTS.search(m):
            # Credit to card = reduces outstanding → payment or refund
            if _REFUND_HINTS.search(m):
                return TransactionType.REFUND
            return TransactionType.PAYMENT_TO_ISSUER
    if _REFUND_HINTS.search(m):
        return TransactionType.REFUND
    if _INTEREST_HINTS.search(m):
        return TransactionType.INTEREST
    if _FEE_HINTS.search(m):
        return TransactionType.FEE
    return TransactionType.PURCHASE


class GenericTextParser:
    """Fallback parser: line-oriented date + merchant + amount extraction."""

    name = "generic_text"

    def can_parse(self, text: str, *, issuer: str | None = None) -> bool:
        # Always available as fallback if any date-looking line exists
        return bool(re.search(r"\d{1,4}[-/]\d{1,2}[-/]\d{1,4}", text))

    def parse(self, text: str, *, issuer: str | None = None) -> ParseResult:
        lines_out: list[ParsedLine] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or len(line) < 8:
                continue
            # Collapse multi-spaces
            compact = re.sub(r"\s+", " ", line)
            match = _LINE_RE.match(compact)
            if not match:
                continue
            day = _parse_date_token(match.group("date"))
            if day is None:
                continue
            merchant = (match.group("merchant") or "Unknown").strip()[:255]
            amount_paise = _rupees_to_paise(match.group("amount"))
            if amount_paise <= 0:
                continue
            # Skip pure totals / balance rows
            if re.search(r"\b(total|balance|minimum\s*due|credit\s*limit)\b", merchant, re.I):
                continue
            proposed = _infer_type(merchant, match.group("crdr"))
            occurred = datetime.combine(day, time(12, 0), tzinfo=IST)
            lines_out.append(
                ParsedLine(
                    occurred_at=occurred,
                    merchant=merchant,
                    amount_paise=amount_paise,
                    proposed_type=proposed,
                    raw={"source": "generic_text", "line": raw_line},
                )
            )

        return ParseResult(
            lines=lines_out,
            parser_name=self.name,
            notes=f"Parsed {len(lines_out)} lines via generic text parser",
        )
