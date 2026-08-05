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


class _ImportSession:
    """Records adds and returns queued execute results for import_statement."""

    def __init__(self, execute_results: list[object]) -> None:
        self._results = list(execute_results)
        self.added: list[object] = []
        self.flush_count = 0

    async def execute(self, _stmt: object) -> _FakeResult:
        if not self._results:
            return _FakeResult([])
        return _FakeResult(self._results.pop(0))

    def add(self, obj: object) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        self.flush_count += 1


@pytest.mark.asyncio
async def test_import_confirm_creates_posted_transactions_only() -> None:
    from app.models.enums import PostingStatus
    from app.models.transaction import Transaction

    org_id = uuid4()
    statement_id = uuid4()
    card_id = uuid4()
    statement = SimpleNamespace(
        status=StatementStatus.NEEDS_REVIEW,
        id=statement_id,
        organization_id=org_id,
        credit_card_id=card_id,
    )
    line = SimpleNamespace(
        merchant="Swiggy",
        amount_paise=245_00,
        occurred_at=datetime.now(UTC),
        proposed_type=TransactionType.PURCHASE,
        proposed_contact_id=None,
        review_status=LineReviewStatus.ACCEPTED,
        committed_transaction_id=None,
    )
    # 1) account resolve  2) accepted lines  3) remaining pending  4) all lines
    account_id = uuid4()
    db = _ImportSession([account_id, [line], [], [line]])

    result = await statement_service.import_statement(
        db,  # type: ignore[arg-type]
        statement=statement,  # type: ignore[arg-type]
        user_id=uuid4(),
    )
    assert result == {"created": 1, "skipped": 0}

    txs = [obj for obj in db.added if isinstance(obj, Transaction)]
    assert len(txs) == 1
    assert txs[0].posting_status == PostingStatus.POSTED
    assert txs[0].posting_status != PostingStatus.DRAFT
    assert txs[0].amount_paise == 245_00
    assert txs[0].merchant == "Swiggy"
    assert txs[0].account_id == account_id
    assert line.committed_transaction_id == txs[0].id


@pytest.mark.asyncio
async def test_posted_transaction_from_import_line_helper() -> None:
    from app.models.enums import PostingStatus

    statement = SimpleNamespace(
        id=uuid4(),
        organization_id=uuid4(),
        credit_card_id=uuid4(),
    )
    line = SimpleNamespace(
        merchant="Netflix",
        amount_paise=649_00,
        occurred_at=datetime.now(UTC),
        proposed_type=TransactionType.PURCHASE,
        proposed_contact_id=None,
    )
    tx = statement_service._posted_transaction_from_import_line(
        statement=statement,  # type: ignore[arg-type]
        line=line,  # type: ignore[arg-type]
        user_id=uuid4(),
        account_id=uuid4(),
    )
    assert tx.posting_status is PostingStatus.POSTED
    assert tx.type is TransactionType.PURCHASE
