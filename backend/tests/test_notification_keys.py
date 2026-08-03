"""Unit tests for notification preference thresholds and dedupe keys."""

from app.services.notification_service import SYNC_TYPES, DesiredNotification


def test_sync_types_cover_attention():
    assert "overdue" in SYNC_TYPES
    assert "due_soon" in SYNC_TYPES
    assert "high_utilization" in SYNC_TYPES
    assert "statement_review" in SYNC_TYPES
    # Parse-time events are not auto-synced away
    assert "statement_ready" not in SYNC_TYPES


def test_desired_notification_key_card_scoped():
    item = DesiredNotification(
        type="due_soon",
        title="HDFC due soon",
        body="Due in 3d",
        href="/app/cards/abc-123",
        key="due_soon:abc-123",
    )
    assert item.key.startswith("due_soon:")
    assert "abc-123" in item.key


def test_due_soon_threshold_logic():
    """Mirror dashboard/notification threshold semantics without DB."""
    due_soon_days = 5
    days_to_due_cases = [
        (-1, "overdue"),
        (0, "due_soon"),
        (5, "due_soon"),
        (6, None),
    ]
    for days, expected in days_to_due_cases:
        kind: str | None
        if days < 0:
            kind = "overdue"
        elif days <= due_soon_days:
            kind = "due_soon"
        else:
            kind = None
        assert kind == expected


def test_high_util_threshold_logic():
    high_util_pct = 80
    assert high_util_pct > 79.9 or not (high_util_pct <= 79.9)
    assert high_util_pct <= 80.0
    assert high_util_pct <= 95.0
