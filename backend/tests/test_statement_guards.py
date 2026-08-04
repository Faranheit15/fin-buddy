"""Unit tests for statement import / review guards."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import AppError
from app.models.enums import LineReviewStatus, StatementStatus, TransactionType
from app.services import statement_service


class _FakeResult:
    def __init__(self, value: object) -> None:
        self._value = value

    def scalar_one_or_none(self) -> object:
        return self._value

    def scalars(self) -> SimpleNamespace:
        return SimpleNamespace(all=lambda: self._value if isinstance(self._value, list) else [])


class _FakeSession:
    def __init__(self, statement: object, line: object | None = None) -> None:
        self._statement = statement
        self._line = line
        self._calls = 0

    async def execute(self, _stmt: object) -> _FakeResult:
        self._calls += 1
        if self._calls == 1:
            return _FakeResult(self._statement)
        return _FakeResult(self._line)


@pytest.mark.asyncio
async def test_update_line_rejects_imported_statement() -> None:
    statement = SimpleNamespace(status=StatementStatus.IMPORTED)
    db = _FakeSession(statement)

    with pytest.raises(AppError) as exc:
        await statement_service.update_line(
            db,  # type: ignore[arg-type]
            org_id=uuid4(),
            statement_id=uuid4(),
            line_id=uuid4(),
            merchant="Nope",
        )
    assert exc.value.code == "statement_already_imported"


@pytest.mark.asyncio
async def test_import_statement_is_idempotent_when_already_imported() -> None:
    statement = SimpleNamespace(
        status=StatementStatus.IMPORTED,
        id=uuid4(),
        organization_id=uuid4(),
        credit_card_id=uuid4(),
    )
    result = await statement_service.import_statement(
        None,  # type: ignore[arg-type]
        statement=statement,  # type: ignore[arg-type]
        user_id=uuid4(),
    )
    assert result == {"created": 0, "skipped": 0}


@pytest.mark.asyncio
async def test_update_line_rejects_committed_line() -> None:
    statement = SimpleNamespace(status=StatementStatus.NEEDS_REVIEW)
    line = SimpleNamespace(
        committed_transaction_id=uuid4(),
        merchant="X",
        amount_paise=100,
        occurred_at=datetime.now(UTC),
        proposed_type=TransactionType.PURCHASE,
        review_status=LineReviewStatus.ACCEPTED,
        proposed_contact_id=None,
    )
    db = _FakeSession(statement, line)

    with pytest.raises(AppError) as exc:
        await statement_service.update_line(
            db,  # type: ignore[arg-type]
            org_id=uuid4(),
            statement_id=uuid4(),
            line_id=uuid4(),
            merchant="Changed",
        )
    assert exc.value.code == "line_already_imported"
