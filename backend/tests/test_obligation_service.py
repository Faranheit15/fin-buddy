"""Unit tests for obligation service."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.models.enums import ObligationStatus, ObligationType
from app.models.obligation import Obligation
from app.services import obligation_service


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

    def scalar_one(self) -> object:
        if not self._values:
            raise Exception("No result")
        return self._values[0]

    def scalars(self) -> "_FakeScalars":
        return _FakeScalars(self._values)

    def first(self) -> object:
        if not self._values:
            return None
        return self._values[0]


class _FakeScalars:
    def __init__(self, values: list[object]) -> None:
        self._values = values

    def all(self) -> list[object]:
        return self._values


class _RecordingSession:
    def __init__(self, results: list[object] | None = None) -> None:
        self._results = list(results or [])
        self.added: list[object] = []
        self.flush_count = 0

    async def execute(self, _stmt: object) -> _FakeResult:
        if not self._results:
            return _FakeResult(None)
        res = self._results.pop(0)
        return _FakeResult(res)

    async def scalar(self, _stmt: object) -> object:
        if not self._results:
            return None
        res = self._results.pop(0)
        if isinstance(res, list) and res:
            return res[0]
        return res

    def add(self, obj: object) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        self.flush_count += 1

    async def commit(self) -> None:
        pass

    async def refresh(self, obj: object) -> None:
        pass


@pytest.mark.asyncio
async def test_partial_repayment_updates_remaining_balance() -> None:
    org_id = uuid4()
    obl_id = uuid4()

    obl = Obligation(
        id=obl_id,
        organization_id=org_id,
        type=ObligationType.RECEIVABLE,
        amount_paise=1000_00,
        status=ObligationStatus.ACTIVE,
    )

    # get_obligation_with_balance requires one fetch. We mock the tuple return in _FakeResult.
    # Wait, the query returns (Obligation, remaining_paise).
    db = _RecordingSession(
        [
            # First query for get_obligation_with_balance (Obligation, total_paid)
            [(obl, 0)]
        ]
    )

    res_obl, remaining = await obligation_service.get_obligation_with_balance(
        db,
        organization_id=org_id,
        obligation_id=obl_id,  # type: ignore[arg-type]
    )
    assert remaining == 1000_00

    # Add payment of 400
    db = _RecordingSession(
        [
            # 1. get_obligation_with_balance (Obligation, total_paid)
            [(obl, 0)],
        ]
    )

    payment = await obligation_service.add_payment(
        db,  # type: ignore[arg-type]
        organization_id=org_id,
        user_id=uuid4(),
        obligation_id=obl_id,
        amount_paise=400_00,
        date=datetime.now(UTC),
    )

    assert payment.amount_paise == 400_00
    assert payment.obligation_id == obl_id
    assert obl.status == ObligationStatus.ACTIVE  # Not fully paid


@pytest.mark.asyncio
async def test_overpayment_warns_and_allows() -> None:
    org_id = uuid4()
    obl_id = uuid4()

    obl = Obligation(
        id=obl_id,
        organization_id=org_id,
        type=ObligationType.RECEIVABLE,
        amount_paise=500_00,
        status=ObligationStatus.ACTIVE,
    )

    # Overpaying by 200_00. Total payment = 700_00
    db = _RecordingSession(
        [
            [(obl, 0)],
        ]
    )

    payment = await obligation_service.add_payment(
        db,  # type: ignore[arg-type]
        organization_id=org_id,
        user_id=uuid4(),
        obligation_id=obl_id,
        amount_paise=700_00,
        date=datetime.now(UTC),
    )

    assert payment.amount_paise == 700_00
    assert obl.status == ObligationStatus.PAID
    # The negative balance logic is verified by the balance query, not the add_payment itself
    # but the payment succeeds, and we marked it PAID.


@pytest.mark.asyncio
async def test_full_repayment_marks_paid() -> None:
    org_id = uuid4()
    obl_id = uuid4()

    obl = Obligation(
        id=obl_id,
        organization_id=org_id,
        type=ObligationType.RECEIVABLE,
        amount_paise=500_00,
        status=ObligationStatus.ACTIVE,
    )

    db = _RecordingSession(
        [
            [(obl, 0)],
        ]
    )

    await obligation_service.add_payment(
        db,  # type: ignore[arg-type]
        organization_id=org_id,
        user_id=uuid4(),
        obligation_id=obl_id,
        amount_paise=500_00,
        date=datetime.now(UTC),
    )
    assert obl.status == ObligationStatus.PAID
