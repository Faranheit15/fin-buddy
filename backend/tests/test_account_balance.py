"""Unit tests for asset/account contribution math and Correct Balance service."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import AppError, NotFoundError
from app.domain.ledger import (
    account_contribution_paise,
    asset_contribution_paise,
)
from app.models.enums import AccountKind, PostingStatus, TransactionType
from app.models.transaction import Transaction
from app.services import account_service


def test_asset_purchase_decreases_cash() -> None:
    assert (
        asset_contribution_paise(
            tx_type=TransactionType.PURCHASE,
            amount_paise=100_00,
            posting_status=PostingStatus.POSTED,
        )
        == -100_00
    )


def test_asset_refund_increases_cash() -> None:
    assert (
        asset_contribution_paise(
            tx_type=TransactionType.REFUND,
            amount_paise=40_00,
            posting_status=PostingStatus.POSTED,
        )
        == 40_00
    )


def test_asset_payment_to_issuer_decreases_cash() -> None:
    assert (
        asset_contribution_paise(
            tx_type=TransactionType.PAYMENT_TO_ISSUER,
            amount_paise=500_00,
            posting_status=PostingStatus.POSTED,
        )
        == -500_00
    )


def test_asset_interest_increases_cash() -> None:
    assert (
        asset_contribution_paise(
            tx_type=TransactionType.INTEREST,
            amount_paise=12_00,
            posting_status=PostingStatus.POSTED,
        )
        == 12_00
    )


def test_asset_draft_excluded() -> None:
    assert (
        asset_contribution_paise(
            tx_type=TransactionType.PURCHASE,
            amount_paise=100_00,
            posting_status=PostingStatus.DRAFT,
        )
        == 0
    )


def test_asset_adjustment_signed() -> None:
    assert (
        asset_contribution_paise(
            tx_type=TransactionType.ADJUSTMENT,
            amount_paise=75_00,
            posting_status=PostingStatus.POSTED,
            delta_sign=-1,
        )
        == -75_00
    )


def test_asset_reversal_of_purchase_restores_cash() -> None:
    amount = 90_00
    spend = asset_contribution_paise(
        tx_type=TransactionType.PURCHASE,
        amount_paise=amount,
        posting_status=PostingStatus.POSTED,
    )
    reversal = asset_contribution_paise(
        tx_type=TransactionType.REVERSAL,
        amount_paise=amount,
        posting_status=PostingStatus.POSTED,
        original_type=TransactionType.PURCHASE,
    )
    assert spend + reversal == 0


def test_account_contribution_routes_by_kind() -> None:
    purchase = 50_00
    assert (
        account_contribution_paise(
            kind=AccountKind.CREDIT_CARD,
            tx_type=TransactionType.PURCHASE,
            amount_paise=purchase,
            posting_status=PostingStatus.POSTED,
        )
        == purchase
    )
    assert (
        account_contribution_paise(
            kind=AccountKind.CASH,
            tx_type=TransactionType.PURCHASE,
            amount_paise=purchase,
            posting_status=PostingStatus.POSTED,
        )
        == -purchase
    )


class _FakeResult:
    def __init__(self, value: object) -> None:
        self._value = value

    def scalar_one_or_none(self) -> object:
        return self._value

    def scalar_one(self) -> object:
        return self._value


class _RecordingSession:
    def __init__(self, results: list[object] | None = None) -> None:
        self._results = list(results or [])
        self.added: list[object] = []
        self.flush_count = 0

    async def execute(self, _stmt: object) -> _FakeResult:
        if not self._results:
            return _FakeResult(None)
        return _FakeResult(self._results.pop(0))

    def add(self, obj: object) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        self.flush_count += 1


def _cash_account(**overrides: object) -> SimpleNamespace:
    base = {
        "id": uuid4(),
        "organization_id": uuid4(),
        "kind": AccountKind.CASH,
        "name": "Wallet",
        "institution": None,
        "currency": "INR",
        "credit_card_id": None,
        "archived_at": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_correct_balance_posts_adjustment_to_target() -> None:
    org_id = uuid4()
    account = _cash_account(organization_id=org_id)
    # 1) get_account  2) account_balance_paise current=100_00
    db = _RecordingSession([account, 100_00])
    tx = await account_service.correct_balance(
        db,  # type: ignore[arg-type]
        organization_id=org_id,
        user_id=uuid4(),
        account_id=account.id,
        target_balance_paise=250_00,
        reason="Reconcile with cash count",
    )
    assert isinstance(tx, Transaction)
    assert tx.type == TransactionType.ADJUSTMENT
    assert tx.posting_status == PostingStatus.POSTED
    assert tx.account_id == account.id
    assert tx.credit_card_id is None
    assert tx.amount_paise == 150_00
    assert tx.delta_sign == 1
    assert tx.correction_reason == "Reconcile with cash count"
    assert any(obj is tx for obj in db.added)


@pytest.mark.asyncio
async def test_correct_balance_negative_delta() -> None:
    org_id = uuid4()
    account = _cash_account(organization_id=org_id)
    db = _RecordingSession([account, 200_00])
    tx = await account_service.correct_balance(
        db,  # type: ignore[arg-type]
        organization_id=org_id,
        user_id=uuid4(),
        account_id=account.id,
        target_balance_paise=50_00,
        reason="Spent cash not logged",
    )
    assert tx.amount_paise == 150_00
    assert tx.delta_sign == -1


@pytest.mark.asyncio
async def test_correct_balance_already_at_target() -> None:
    org_id = uuid4()
    account = _cash_account(organization_id=org_id)
    db = _RecordingSession([account, 100_00])
    with pytest.raises(AppError) as exc:
        await account_service.correct_balance(
            db,  # type: ignore[arg-type]
            organization_id=org_id,
            user_id=uuid4(),
            account_id=account.id,
            target_balance_paise=100_00,
            reason="noop",
        )
    assert exc.value.code == "already_at_target"


@pytest.mark.asyncio
async def test_correct_balance_archived_blocked() -> None:
    org_id = uuid4()
    account = _cash_account(
        organization_id=org_id,
        archived_at=datetime.now(UTC),
    )
    db = _RecordingSession([account])
    with pytest.raises(AppError) as exc:
        await account_service.correct_balance(
            db,  # type: ignore[arg-type]
            organization_id=org_id,
            user_id=uuid4(),
            account_id=account.id,
            target_balance_paise=10_00,
            reason="should fail",
        )
    assert exc.value.code == "account_archived"


@pytest.mark.asyncio
async def test_correct_balance_missing_account() -> None:
    db = _RecordingSession([None])
    with pytest.raises(NotFoundError):
        await account_service.correct_balance(
            db,  # type: ignore[arg-type]
            organization_id=uuid4(),
            user_id=uuid4(),
            account_id=uuid4(),
            target_balance_paise=10_00,
            reason="missing",
        )


@pytest.mark.asyncio
async def test_correct_balance_card_account_sets_credit_card_id() -> None:
    org_id = uuid4()
    card_id = uuid4()
    account = _cash_account(
        organization_id=org_id,
        kind=AccountKind.CREDIT_CARD,
        credit_card_id=card_id,
        name="HDFC",
    )
    # get_account, balance, ensure_card
    db = _RecordingSession([account, 300_00, card_id])
    tx = await account_service.correct_balance(
        db,  # type: ignore[arg-type]
        organization_id=org_id,
        user_id=uuid4(),
        account_id=account.id,
        target_balance_paise=250_00,
        reason="Match statement outstanding",
    )
    assert tx.credit_card_id == card_id
    assert tx.amount_paise == 50_00
    assert tx.delta_sign == -1
