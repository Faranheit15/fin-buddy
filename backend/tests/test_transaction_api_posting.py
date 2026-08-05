"""Service tests for draft/posted immutability, reverse, and adjust."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.domain.ledger import card_contribution_paise, contact_contribution_paise
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
    """T4: PATCH posted → 409 posted_immutable."""
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
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_delete_posted_raises_immutable() -> None:
    """T4: DELETE posted → 409 posted_immutable."""
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
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_update_draft_allows_merchant_change() -> None:
    """T4: PATCH draft merchant OK."""
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
async def test_delete_draft_ok() -> None:
    """T4: DELETE draft succeeds (service deletes row)."""
    tx = _posted_purchase(posting_status=PostingStatus.DRAFT)
    db = _RecordingSession([tx])
    await transaction_service.delete_transaction(
        db,  # type: ignore[arg-type]
        organization_id=tx.organization_id,
        user_id=uuid4(),
        transaction_id=tx.id,
    )
    assert any(obj is tx for obj in db.deleted)
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
async def test_post_draft_then_amount_enters_outstanding() -> None:
    """T1: posting a draft flips contribution from 0 to amount_paise."""
    amount = 150_00
    tx = _posted_purchase(posting_status=PostingStatus.DRAFT, amount_paise=amount)
    assert (
        card_contribution_paise(
            tx_type=TransactionType.PURCHASE,
            amount_paise=amount,
            posting_status=PostingStatus.DRAFT,
        )
        == 0
    )
    db = _RecordingSession([tx])
    posted = await transaction_service.post_draft(
        db,  # type: ignore[arg-type]
        organization_id=tx.organization_id,
        user_id=uuid4(),
        transaction_id=tx.id,
    )
    assert posted.posting_status == PostingStatus.POSTED
    assert (
        card_contribution_paise(
            tx_type=TransactionType.PURCHASE,
            amount_paise=posted.amount_paise,
            posting_status=posted.posting_status,
        )
        == amount
    )


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
    """T4: reverse posted + reason → links set; net outstanding 0."""
    org_id = uuid4()
    card_id = uuid4()
    original = _posted_purchase(organization_id=org_id, credit_card_id=card_id, amount_paise=250_00)
    before = card_contribution_paise(
        tx_type=TransactionType.PURCHASE,
        amount_paise=original.amount_paise,
        posting_status=PostingStatus.POSTED,
    )
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
    after_reversal = card_contribution_paise(
        tx_type=TransactionType.REVERSAL,
        amount_paise=reversal.amount_paise,
        posting_status=PostingStatus.POSTED,
        original_type=TransactionType.PURCHASE,
    )
    assert before + after_reversal == 0


@pytest.mark.asyncio
async def test_double_reverse_blocked_after_successful_reverse() -> None:
    """T2: Reverse once, then reverse again → already_reversed; only one reversal row."""
    org_id = uuid4()
    original = _posted_purchase(organization_id=org_id, amount_paise=100_00)
    db = _RecordingSession([original])
    first = await transaction_service.reverse_transaction(
        db,  # type: ignore[arg-type]
        organization_id=org_id,
        user_id=uuid4(),
        transaction_id=original.id,
        reason="First reverse",
    )
    assert original.reversed_by_id == first.id
    # Second reverse: get_transaction returns the already-linked original
    db2 = _RecordingSession([original])
    with pytest.raises(ConflictError) as exc:
        await transaction_service.reverse_transaction(
            db2,  # type: ignore[arg-type]
            organization_id=org_id,
            user_id=uuid4(),
            transaction_id=original.id,
            reason="Second reverse",
        )
    assert exc.value.code == "already_reversed"
    assert not any(getattr(obj, "type", None) == TransactionType.REVERSAL for obj in db2.added)


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
    """T3: delta_paise=0 → invalid_delta."""
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
async def test_adjust_positive_delta_increases_outstanding() -> None:
    """T4/T3: adjust(+150_00) with card in org → posted adjustment; contrib +150_00."""
    org_id = uuid4()
    card_id = uuid4()
    db = _RecordingSession([card_id])
    tx = await transaction_service.adjust_balance(
        db,  # type: ignore[arg-type]
        organization_id=org_id,
        user_id=uuid4(),
        credit_card_id=card_id,
        delta_paise=150_00,
        reason="Raise balance",
    )
    assert tx.type == TransactionType.ADJUSTMENT
    assert tx.posting_status == PostingStatus.POSTED
    assert tx.amount_paise == 150_00
    assert tx.delta_sign == 1
    assert (
        card_contribution_paise(
            tx_type=tx.type,
            amount_paise=tx.amount_paise,
            posting_status=tx.posting_status,
            delta_sign=tx.delta_sign,
        )
        == 150_00
    )


@pytest.mark.asyncio
async def test_adjust_negative_delta_decreases_outstanding() -> None:
    """T3: adjust(-75_00) → outstanding −75_00; delta_sign=-1; amount_paise=75_00."""
    org_id = uuid4()
    card_id = uuid4()
    db = _RecordingSession([card_id])
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
    assert (
        card_contribution_paise(
            tx_type=tx.type,
            amount_paise=tx.amount_paise,
            posting_status=tx.posting_status,
            delta_sign=tx.delta_sign,
        )
        == -75_00
    )


@pytest.mark.asyncio
async def test_adjust_with_contact_moves_card_and_contact() -> None:
    """T3: adjust + contact_id → card and contact balances move by signed delta."""
    org_id = uuid4()
    card_id = uuid4()
    contact_id = uuid4()
    db = _RecordingSession([card_id, contact_id])
    tx = await transaction_service.adjust_balance(
        db,  # type: ignore[arg-type]
        organization_id=org_id,
        user_id=uuid4(),
        credit_card_id=card_id,
        contact_id=contact_id,
        delta_paise=40_00,
        reason="Assign contact adjustment",
    )
    assert tx.contact_id == contact_id
    assert tx.delta_sign == 1
    assert (
        card_contribution_paise(
            tx_type=tx.type,
            amount_paise=tx.amount_paise,
            posting_status=tx.posting_status,
            delta_sign=tx.delta_sign,
        )
        == 40_00
    )
    assert (
        contact_contribution_paise(
            tx_type=tx.type,
            amount_paise=tx.amount_paise,
            posting_status=tx.posting_status,
            contact_id_present=True,
            delta_sign=tx.delta_sign,
        )
        == 40_00
    )


@pytest.mark.asyncio
async def test_create_rejects_adjustment_type() -> None:
    """T4: create type=adjustment → invalid_posting_type."""
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
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_rejects_reversal_type() -> None:
    """T4: create type=reversal → invalid_posting_type."""
    db = _RecordingSession()
    with pytest.raises(AppError) as exc:
        await transaction_service.create_transaction(
            db,  # type: ignore[arg-type]
            organization_id=uuid4(),
            user_id=uuid4(),
            credit_card_id=uuid4(),
            tx_type=TransactionType.REVERSAL,
            amount_paise=10_00,
            occurred_at=datetime.now(UTC),
            merchant="X",
        )
    assert exc.value.code == "invalid_posting_type"


@pytest.mark.asyncio
async def test_create_defaults_to_posted_and_moves_balance() -> None:
    """T4: create without posting_status → posted; outstanding moves."""
    org_id = uuid4()
    card_id = uuid4()
    amount = 120_00
    db = _RecordingSession([card_id])
    tx = await transaction_service.create_transaction(
        db,  # type: ignore[arg-type]
        organization_id=org_id,
        user_id=uuid4(),
        credit_card_id=card_id,
        tx_type=TransactionType.PURCHASE,
        amount_paise=amount,
        occurred_at=datetime.now(UTC),
        merchant="Default posted",
    )
    assert tx.posting_status == PostingStatus.POSTED
    assert any(obj is tx for obj in db.added)
    assert (
        card_contribution_paise(
            tx_type=tx.type,
            amount_paise=tx.amount_paise,
            posting_status=tx.posting_status,
        )
        == amount
    )


@pytest.mark.asyncio
async def test_create_draft_does_not_move_balance() -> None:
    """T4: create posting_status=draft → balances unchanged (contrib 0)."""
    org_id = uuid4()
    card_id = uuid4()
    amount = 55_00
    db = _RecordingSession([card_id])
    tx = await transaction_service.create_transaction(
        db,  # type: ignore[arg-type]
        organization_id=org_id,
        user_id=uuid4(),
        credit_card_id=card_id,
        tx_type=TransactionType.PURCHASE,
        amount_paise=amount,
        occurred_at=datetime.now(UTC),
        merchant="Draft only",
        posting_status=PostingStatus.DRAFT,
    )
    assert tx.posting_status == PostingStatus.DRAFT
    assert (
        card_contribution_paise(
            tx_type=tx.type,
            amount_paise=tx.amount_paise,
            posting_status=tx.posting_status,
        )
        == 0
    )


@pytest.mark.asyncio
async def test_create_wrong_card_not_found() -> None:
    """T4: card not in org → NotFoundError (cross-org / wrong card)."""
    db = _RecordingSession([None])
    with pytest.raises(NotFoundError):
        await transaction_service.create_transaction(
            db,  # type: ignore[arg-type]
            organization_id=uuid4(),
            user_id=uuid4(),
            credit_card_id=uuid4(),
            tx_type=TransactionType.PURCHASE,
            amount_paise=10_00,
            occurred_at=datetime.now(UTC),
            merchant="Foreign card",
        )


@pytest.mark.asyncio
async def test_adjust_wrong_card_not_found() -> None:
    """T4: adjust with card outside org → NotFoundError."""
    db = _RecordingSession([None])
    with pytest.raises(NotFoundError):
        await transaction_service.adjust_balance(
            db,  # type: ignore[arg-type]
            organization_id=uuid4(),
            user_id=uuid4(),
            credit_card_id=uuid4(),
            delta_paise=10_00,
            reason="Foreign adjust",
        )


@pytest.mark.asyncio
async def test_reverse_foreign_org_not_found() -> None:
    """T4: reverse tx from another org → NotFoundError."""
    tx = _posted_purchase()
    db = _RecordingSession([None])  # get_transaction scoped miss
    with pytest.raises(NotFoundError):
        await transaction_service.reverse_transaction(
            db,  # type: ignore[arg-type]
            organization_id=uuid4(),
            user_id=uuid4(),
            transaction_id=tx.id,
            reason="Wrong org",
        )


@pytest.mark.asyncio
async def test_get_missing_raises_not_found() -> None:
    db = _RecordingSession([None])
    with pytest.raises(NotFoundError):
        await transaction_service.get_transaction(db, uuid4(), uuid4())  # type: ignore[arg-type]
