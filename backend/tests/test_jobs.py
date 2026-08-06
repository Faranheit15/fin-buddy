"""Tests for background jobs (reminders)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.models.organization import Organization, OrganizationMember
from app.models.credit_card import CreditCard
from app.models.enums import CardStatus, DueRuleType

class _FakeResult:
    def __init__(self, values: list[object] | object = None) -> None:
        if isinstance(values, list):
            self._values = values
        else:
            self._values = [values] if values is not None else []
            
    def scalar_one_or_none(self) -> object:
        if not self._values:
            return None
        return self._values[0]

    def scalars(self) -> "_FakeScalars":
        return _FakeScalars(self._values)

    def all(self) -> list[object]:
        return self._values

class _FakeScalars:
    def __init__(self, values: list[object]) -> None:
        self._values = values
    def all(self) -> list[object]:
        return self._values
    def first(self) -> object:
        if not self._values:
            return None
        return self._values[0]

class _RecordingSession:
    def __init__(self, results: list[object] | None = None) -> None:
        self._results = list(results or [])

    async def execute(self, _stmt: object) -> _FakeResult:
        if not self._results:
            return _FakeResult(None)
        res = self._results.pop(0)
        return _FakeResult(res)


@pytest.mark.asyncio
async def test_send_reminders_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 1. Track emails
    sent_emails = []

    async def mock_send_email(settings, to_email, subject, text_body, html_body=None):
        sent_emails.append((to_email, subject, text_body))

    monkeypatch.setattr("app.api.v1.jobs.send_email", mock_send_email)

    # 2. Setup user and data directly in DB
    # We create a profile with due_soon_days = 7
    # One card due in 5 days (should include)
    # One card due in 10 days (should exclude)
    
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    IST = ZoneInfo("Asia/Kolkata")
    today = datetime.now(IST).date()

    from uuid import uuid4
    user_id = uuid4()
    org_id = uuid4()

    profile = Profile(
        id=user_id,
        email="test_reminders@example.com",
        due_soon_days=7,
        email_reminders_enabled=True,
        is_active=True,
        timezone="Asia/Kolkata"
    )
    org = Organization(id=org_id, name="Test Org", slug="test-org")
    member = OrganizationMember(organization_id=org_id, user_id=user_id)

    # due in 5 days
    due_5_date = today + timedelta(days=5)
    card_5 = CreditCard(
        id=uuid4(),
        organization_id=org_id,
        nickname="Due Soon Card",
        issuer="Bank",
        network="visa",
        credit_limit_paise=10000000,
        statement_day=1, # doesn't matter much if we set next_due_date logic
        due_rule_type=DueRuleType.FIXED_DAY,
        due_rule_value=due_5_date.day, # simplistic
        status=CardStatus.ACTIVE,
    )

    # Need to make sure next_due_date calculation matches our expected days_to_due.
    # add a card out of range
    card_15 = CreditCard(
        id=uuid4(),
        organization_id=org_id,
        nickname="Far Due Card",
        issuer="Bank",
        network="visa",
        credit_limit_paise=10000000,
        statement_day=2, 
        due_rule_type=DueRuleType.FIXED_DAY,
        due_rule_value=1,
        status=CardStatus.ACTIVE,
    )

    # Mock db queries
    db = _RecordingSession([
        # 1. profiles
        [profile],
        # 2. orgs
        [(org_id,)],
        # 3. cards
        [card_5, card_15],
        # 4. EMIs (empty)
        []
    ])

    # 3. Call endpoint directly
    from app.api.v1.jobs import send_reminders
    from app.core.config import Settings
    settings = Settings()
    
    # We must also mock cards_outstanding_map
    async def mock_outstanding_map(db_session, org_id):
        return {card_5.id: 500000, card_15.id: 1000000}
        
    def mock_next_due(today_d, statement_day, due_rule_type, due_rule_value):
        if statement_day == 1:
            return due_5_date
        return today_d + timedelta(days=15) # out of range

    monkeypatch.setattr("app.api.v1.jobs.cards_outstanding_map", mock_outstanding_map)
    monkeypatch.setattr("app.api.v1.jobs.next_due_date_for_card", mock_next_due)

    res = await send_reminders(db, settings) # type: ignore[arg-type]
    assert "Reminders sent to 1 users" in res.message

    # 4. Verify email
    # It should send 1 email to test_reminders@example.com
    # The text should include "Due Soon Card" and NOT "Far Due Card"
    found = False
    for to_email, subject, text_body in sent_emails:
        if to_email == "test_reminders@example.com":
            found = True
            assert "Due Soon Card" in text_body
            assert "Far Due Card" not in text_body
            assert "5,000.00" in text_body
            assert "in 5 days" in text_body
            break
    
    assert found, "Expected reminder email was not sent"
