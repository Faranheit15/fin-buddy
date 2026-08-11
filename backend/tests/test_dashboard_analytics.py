from datetime import date

from app.services.dashboard_analytics import _month_starts


def test_month_starts_returns_six_consecutive_calendar_months() -> None:
    assert _month_starts(date(2026, 1, 18)) == [
        date(2025, 8, 1),
        date(2025, 9, 1),
        date(2025, 10, 1),
        date(2025, 11, 1),
        date(2025, 12, 1),
        date(2026, 1, 1),
    ]
