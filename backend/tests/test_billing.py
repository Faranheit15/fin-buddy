"""Billing cycle pure-function tests."""

from datetime import date

import pytest
from app.domain.billing import (
    DueRuleType,
    clamp_day_of_month,
    compute_due_date,
    next_occurrence_of_day,
    previous_occurrence_of_day,
)


def test_clamp_day_of_month_february() -> None:
    assert clamp_day_of_month(2026, 2, 31) == date(2026, 2, 28)


def test_next_occurrence_same_month() -> None:
    assert next_occurrence_of_day(date(2026, 7, 1), 15) == date(2026, 7, 15)


def test_next_occurrence_rolls_month() -> None:
    assert next_occurrence_of_day(date(2026, 7, 16), 15) == date(2026, 8, 15)


def test_previous_occurrence() -> None:
    assert previous_occurrence_of_day(date(2026, 7, 20), 15) == date(2026, 7, 15)
    assert previous_occurrence_of_day(date(2026, 7, 10), 15) == date(2026, 6, 15)


def test_due_date_days_after_statement() -> None:
    due = compute_due_date(
        date(2026, 7, 15),
        rule_type=DueRuleType.DAYS_AFTER_STATEMENT,
        rule_value=20,
    )
    assert due == date(2026, 8, 4)


def test_due_date_fixed_day() -> None:
    due = compute_due_date(
        date(2026, 7, 15),
        rule_type=DueRuleType.FIXED_DAY,
        rule_value=5,
    )
    assert due == date(2026, 8, 5)


def test_invalid_day_raises() -> None:
    with pytest.raises(ValueError):
        next_occurrence_of_day(date(2026, 7, 1), 0)


def test_next_due_for_card_days_after() -> None:
    from app.domain.billing import next_due_date_for_card

    # Statement day 15; today July 20 → last stmt July 15; due = July 15 + 20 = Aug 4
    due = next_due_date_for_card(
        date(2026, 7, 20),
        statement_day=15,
        due_rule_type=DueRuleType.DAYS_AFTER_STATEMENT,
        due_rule_value=20,
    )
    assert due == date(2026, 8, 4)
