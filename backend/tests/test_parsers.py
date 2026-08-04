"""Unit tests for statement parsers."""

from app.models.enums import TransactionType
from app.services.parsers import parse_statement_text, select_parser
from app.services.parsers.finbuddy_sample import FinBuddySampleParser
from app.services.parsers.generic import GenericTextParser

SAMPLE = """
FINBUDDY_STATEMENT
CARD:4821
PERIOD:2026-06-15..2026-07-14
STATEMENT_DATE:2026-07-15
DUE_DATE:2026-08-04
---
2026-07-01|purchase|SWIGGY BANGALORE|2450.00
2026-07-05|purchase|AMAZON PAY|1,299.00
2026-07-10|refund|AMAZON PAY|500.00
2026-07-12|payment_to_issuer|PAYMENT THANK YOU|15000.00
"""

GENERIC = """
Statement for July
01/07/2026  SWIGGY BANGALORE  2,450.00 Dr
05/07/2026  AMAZON PAY INDIA  1,299.00 DR
10/07/2026  AMAZON PAY REFUND  500.00 Cr
12/07/2026  PAYMENT THANK YOU  15,000.00 CR
Total outstanding  99,999.00
"""


def test_select_finbuddy_parser() -> None:
    assert isinstance(select_parser(SAMPLE), FinBuddySampleParser)


def test_finbuddy_sample_parse() -> None:
    result = parse_statement_text(SAMPLE)
    assert result.parser_name == "finbuddy_sample"
    assert len(result.lines) == 4
    assert result.statement_date is not None
    assert result.statement_date.isoformat() == "2026-07-15"
    assert result.due_date is not None
    assert result.lines[0].amount_paise == 245_000
    assert result.lines[0].proposed_type == TransactionType.PURCHASE
    assert result.lines[1].amount_paise == 129_900
    assert result.lines[2].proposed_type == TransactionType.REFUND
    assert result.lines[3].proposed_type == TransactionType.PAYMENT_TO_ISSUER


def test_generic_parse() -> None:
    assert isinstance(select_parser(GENERIC), GenericTextParser)
    result = parse_statement_text(GENERIC)
    assert result.parser_name == "generic_text"
    assert len(result.lines) >= 3
    merchants = " ".join(line.merchant for line in result.lines).upper()
    assert "SWIGGY" in merchants
    # Total row should be skipped
    assert all("total" not in (line.merchant or "").lower() for line in result.lines)


def test_empty_text_no_crash() -> None:
    result = parse_statement_text("hello world no dates")
    assert result.lines == []
