"""Service tests for draft/posted immutability, reverse, and adjust."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.models.enums import PostingStatus, TransactionType
from app.services import transaction_service


class _FakeResult:
    def __init__(self, value: object) -> None:
        self._value = value

    def scalar_one_or_none(self) -> object:
        return self._value


class _RecordingSession:
    """Minimal async session: queued execute results + tracks add/delete/flush."""

    def __init__(self, results: list[object] | None = None) -> None:
        self._results = list(results or [])
        self.added: list[object] = []
        self.deleted: list[object] = []
        self.flush_count = 0

    async def execute(self, _stmt: object) -> _FakeResult:
        if not self._results:
            return _FakeResult(None)
        return _FakeResult(self._results.pop(0))

    def add(self, obj: object) -> None:
        self.added.append(obj)

    async def delete(self, obj: object) -> None:
        self.deleted.append(obj)

    async def flush(self) -> None:
        self.flush_count += 1


def _posted_purchase(**overrides: object) -> SimpleNamespace:
    base = {
        "id": uuid4(),
        "organization_id": uuid4(),
        "credit_card_id": uuid4(),
        "contact_id": None,
        "type": TransactionType.PURCHASE,
        "posting_status": PostingStatus.POSTED,
        "amount_paise": 250_00,
        "currency": "INR",
        "occurred_at": datetime.now(UTC),
        "merchant": "Swiggy",
        "category": None,
        "notes": None,
        "correction_reason": None,
        "delta_sign": None,
        "reverses_id": None,
        "reversed_by_id": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_update_posted_raises_immutable() -> None:
    tx = _posted_purchase()
    db = _RecordingSession([tx])
    with pytest.raises(ConflictError) as exc:
        await transaction_service.update_transaction(
            db,  # type: ignore[arg-type]
            organization_id=tx.organization_id,
            user_id=uuid4(),
            transaction_id=tx.id,
            patch={"merchant": "Nope"},
        )
    assert exc.value.code == "posted_immutable"


@pytest.mark.asyncio
async def test_delete_posted_raises_immutable() -> None:
    tx = _posted_purchase()
    db = _RecordingSession([tx])
    with pytest.raises(ConflictError) as exc:
        await transaction_service.delete_transaction(
            db,  # type: ignore[arg-type]
            organization_id=tx.organization_id,
            user_id=uuid4(),
            transaction_id=tx.id,
        )
    assert exc.value.code == "posted_immutable"


@pytest.mark.asyncio
async def test_update_draft_allows_merchant_change() -> None:
    tx = _posted_purchase(posting_status=PostingStatus.DRAFT)
    db = _RecordingSession([tx])
    updated = await transaction_service.update_transaction(
        db,  # type: ignore[arg-type]
        organization_id=tx.organization_id,
        user_id=uuid4(),
        transaction_id=tx.id,
        patch={"merchant": "Edited"},
    )
    assert updated.merchant == "Edited"
    assert db.flush_count >= 1


@pytest.mark.asyncio
async def test_post_draft_sets_posted() -> None:
    tx = _posted_purchase(posting_status=PostingStatus.DRAFT)
    db = _RecordingSession([tx])
    posted = await transaction_service.post_draft(
        db,  # type: ignore[arg-type]
        organization_id=tx.organization_id,
        user_id=uuid4(),
        transaction_id=tx.id,
    )
    assert posted.posting_status == PostingStatus.POSTED


@pytest.mark.asyncio
async def test_post_already_posted_conflicts() -> None:
    tx = _posted_purchase()
    db = _RecordingSession([tx])
    with pytest.raises(ConflictError) as exc:
        await transaction_service.post_draft(
            db,  # type: ignore[arg-type]
            organization_id=tx.organization_id,
            user_id=uuid4(),
            transaction_id=tx.id,
        )
    assert exc.value.code == "already_posted"


@pytest.mark.asyncio
async def test_reverse_posted_purchase_links_rows() -> None:
    org_id = uuid4()
    card_id = uuid4()
    original = _posted_purchase(organization_id=org_id, credit_card_id=card_id)
    db = _RecordingSession([original])
    reversal = await transaction_service.reverse_transaction(
        db,  # type: ignore[arg-type]
        organization_id=org_id,
        user_id=uuid4(),
        transaction_id=original.id,
        reason="Duplicate charge",
    )
    assert reversal.type == TransactionType.REVERSAL
    assert reversal.posting_status == PostingStatus.POSTED
    assert reversal.reverses_id == original.id
    assert reversal.amount_paise == original.amount_paise
    assert original.reversed_by_id == reversal.id
    assert any(obj is reversal for obj in db.added)


@pytest.mark.asyncio
async def test_double_reverse_blocked() -> None:
    original = _posted_purchase(reversed_by_id=uuid4())
    db = _RecordingSession([original])
    with pytest.raises(ConflictError) as exc:
        await transaction_service.reverse_transaction(
            db,  # type: ignore[arg-type]
            organization_id=original.organization_id,
            user_id=uuid4(),
            transaction_id=original.id,
            reason="Again",
        )
    assert exc.value.code == "already_reversed"


@pytest.mark.asyncio
async def test_cannot_reverse_reversal() -> None:
    original = _posted_purchase(type=TransactionType.REVERSAL)
    db = _RecordingSession([original])
    with pytest.raises(AppError) as exc:
        await transaction_service.reverse_transaction(
            db,  # type: ignore[arg-type]
            organization_id=original.organization_id,
            user_id=uuid4(),
            transaction_id=original.id,
            reason="Nope",
        )
    assert exc.value.code == "cannot_reverse"


@pytest.mark.asyncio
async def test_cannot_reverse_draft() -> None:
    original = _posted_purchase(posting_status=PostingStatus.DRAFT)
    db = _RecordingSession([original])
    with pytest.raises(AppError) as exc:
        await transaction_service.reverse_transaction(
            db,  # type: ignore[arg-type]
            organization_id=original.organization_id,
            user_id=uuid4(),
            transaction_id=original.id,
            reason="Nope",
        )
    assert exc.value.code == "cannot_reverse"


@pytest.mark.asyncio
async def test_adjust_zero_delta_rejected() -> None:
    db = _RecordingSession()
    with pytest.raises(AppError) as exc:
        await transaction_service.adjust_balance(
            db,  # type: ignore[arg-type]
            organization_id=uuid4(),
            user_id=uuid4(),
            credit_card_id=uuid4(),
            delta_paise=0,
            reason="noop",
        )
    assert exc.value.code == "invalid_delta"


@pytest.mark.asyncio
async def test_adjust_creates_signed_posted_row() -> None:
    org_id = uuid4()
    card_id = uuid4()
    db = _RecordingSession([card_id])  # ensure_card finds id
    tx = await transaction_service.adjust_balance(
        db,  # type: ignore[arg-type]
        organization_id=org_id,
        user_id=uuid4(),
        credit_card_id=card_id,
        delta_paise=-75_00,
        reason="Correct balance",
    )
    assert tx.type == TransactionType.ADJUSTMENT
    assert tx.posting_status == PostingStatus.POSTED
    assert tx.amount_paise == 75_00
    assert tx.delta_sign == -1
    assert tx.correction_reason == "Correct balance"


@pytest.mark.asyncio
async def test_create_rejects_adjustment_type() -> None:
    db = _RecordingSession()
    with pytest.raises(AppError) as exc:
        await transaction_service.create_transaction(
            db,  # type: ignore[arg-type]
            organization_id=uuid4(),
            user_id=uuid4(),
            credit_card_id=uuid4(),
            tx_type=TransactionType.ADJUSTMENT,
            amount_paise=10_00,
            occurred_at=datetime.now(UTC),
            merchant="X",
        )
    assert exc.value.code == "invalid_posting_type"


@pytest.mark.asyncio
async def test_get_missing_raises_not_found() -> None:
    db = _RecordingSession([None])
    with pytest.raises(NotFoundError):
        await transaction_service.get_transaction(db, uuid4(), uuid4())  # type: ignore[arg-type]
