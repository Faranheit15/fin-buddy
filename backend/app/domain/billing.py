"""Billing cycle date math (IST-aware pure functions)."""

from calendar import monthrange
from datetime import date, timedelta
from enum import StrEnum


class DueRuleType(StrEnum):
    FIXED_DAY = "fixed_day"
    DAYS_AFTER_STATEMENT = "days_after_statement"


def clamp_day_of_month(year: int, month: int, day: int) -> date:
    """Return a valid date for year/month with day clamped to the month length."""
    last_day = monthrange(year, month)[1]
    return date(year, month, min(day, last_day))


def next_occurrence_of_day(from_date: date, day_of_month: int) -> date:
    """
    Next calendar date on or after `from_date` with the given day-of-month.

    Days 29–31 clamp to the last day of shorter months.
    """
    if day_of_month < 1 or day_of_month > 31:
        raise ValueError("day_of_month must be between 1 and 31")

    candidate = clamp_day_of_month(from_date.year, from_date.month, day_of_month)
    if candidate >= from_date:
        return candidate

    if from_date.month == 12:
        return clamp_day_of_month(from_date.year + 1, 1, day_of_month)
    return clamp_day_of_month(from_date.year, from_date.month + 1, day_of_month)


def previous_occurrence_of_day(from_date: date, day_of_month: int) -> date:
    """Previous calendar date on or before `from_date` with the given day-of-month."""
    if day_of_month < 1 or day_of_month > 31:
        raise ValueError("day_of_month must be between 1 and 31")

    candidate = clamp_day_of_month(from_date.year, from_date.month, day_of_month)
    if candidate <= from_date:
        return candidate

    if from_date.month == 1:
        return clamp_day_of_month(from_date.year - 1, 12, day_of_month)
    return clamp_day_of_month(from_date.year, from_date.month - 1, day_of_month)


def compute_due_date(
    statement_date: date,
    *,
    rule_type: DueRuleType,
    rule_value: int,
) -> date:
    """Compute payment due date from a statement date and rule."""
    if rule_value < 1:
        raise ValueError("rule_value must be >= 1")

    if rule_type is DueRuleType.DAYS_AFTER_STATEMENT:
        return statement_date + timedelta(days=rule_value)

    if rule_type is DueRuleType.FIXED_DAY:
        # Due date is the next occurrence of `rule_value` strictly after statement date
        # when the fixed day would fall on the statement date itself, otherwise on/after.
        return next_occurrence_of_day(statement_date + timedelta(days=1), rule_value)

    raise ValueError(f"Unsupported due rule type: {rule_type}")


def next_statement_date(today: date, statement_day: int) -> date:
    """Next statement generation date on or after today."""
    return next_occurrence_of_day(today, statement_day)


def next_due_date_for_card(
    today: date,
    *,
    statement_day: int,
    due_rule_type: DueRuleType,
    due_rule_value: int,
) -> date:
    """
    Next payment due date for a card.

    Uses the most recent statement date (on or before today) to compute the
    associated due date; if that due date is already past, advances to the
    following cycle.
    """
    last_statement = previous_occurrence_of_day(today, statement_day)
    due = compute_due_date(
        last_statement,
        rule_type=due_rule_type,
        rule_value=due_rule_value,
    )
    if due >= today:
        return due
    next_stmt = next_statement_date(today + timedelta(days=1), statement_day)
    # If statement is today and due already passed, use next statement after today
    if last_statement == today:
        next_stmt = next_occurrence_of_day(today + timedelta(days=1), statement_day)
    return compute_due_date(
        next_stmt if next_stmt > last_statement else next_occurrence_of_day(
            last_statement + timedelta(days=1), statement_day
        ),
        rule_type=due_rule_type,
        rule_value=due_rule_value,
    )
