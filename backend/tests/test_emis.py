"""Unit tests for EMI services."""

from datetime import date
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import AppError
from app.models.emi import EmiInstallment, EmiPlan
from app.models.enums import EmiInstallmentStatus, EmiPlanStatus, TransactionType
from app.services import emi_service
from tests.test_obligation_service import _RecordingSession


def test_emi_schedule_generator() -> None:
    # Test T3: schedule length; sum(principal) ≈ plan principal
    principal = 100000_00  # 100,000.00
    rate_bps = 1500  # 15%
    tenure = 6
    start = date(2026, 1, 1)

    installments = emi_service.generate_emi_schedule(
        principal_paise=principal,
        interest_rate_bps=rate_bps,
        tenure_months=tenure,
        start_date=start,
    )

    assert len(installments) == 6

    # Check sum of principal equals exact original principal
    total_principal = sum(inst.principal_paise for inst in installments)
    assert total_principal == principal

    # Check interest/GST billing effect (T1)
    # Interest + GST are added to total, not block. Principal is blocked.
    for inst in installments:
        assert inst.total_paise == inst.principal_paise + inst.interest_paise + inst.gst_paise
        assert inst.status == EmiInstallmentStatus.PENDING


@pytest.mark.asyncio
async def test_card_emi_blocked_paise() -> None:
    # Test T1/T2: available credit after create and after principal reduction
    db = _RecordingSession([
        # card_emi_blocked_paise returns a scalar (sum of pending principal)
        [50000_00]
    ])

    blocked = await emi_service.card_emi_blocked_paise(
        db, credit_card_id=uuid4()  # type: ignore[arg-type]
    )
    assert blocked == 50000_00


@pytest.mark.asyncio
@patch("app.services.transaction_service.create_transaction")
async def test_pay_emi_installment(mock_create_transaction: AsyncMock) -> None:
    # Test T2: available credit after principal reduction
    org_id = uuid4()
    card_id = uuid4()
    plan_id = uuid4()
    inst_id = uuid4()
    user_id = uuid4()

    plan = EmiPlan(
        id=plan_id,
        organization_id=org_id,
        credit_card_id=card_id,
        principal_paise=10000_00,
        interest_rate_bps=1200,
        tenure_months=3,
        status=EmiPlanStatus.ACTIVE,
    )

    inst = EmiInstallment(
        id=inst_id,
        plan_id=plan_id,
        sequence_number=1,
        due_date=date(2026, 2, 1),
        principal_paise=3300_00,
        interest_paise=100_00,
        gst_paise=18_00,
        fees_paise=0,
        total_paise=3418_00,
        status=EmiInstallmentStatus.PENDING,
    )

    db = _RecordingSession([
        # 1. find installment and plan
        [(inst, plan)],
        # 2. Check if plan is completed (count of pending)
        [2],
    ])

    await emi_service.pay_emi_installment(
        db,  # type: ignore[arg-type]
        organization_id=org_id,
        user_id=user_id,
        installment_id=inst_id,
    )

    assert inst.status == EmiInstallmentStatus.PAID
    assert plan.status == EmiPlanStatus.ACTIVE  # Not completed yet

    assert mock_create_transaction.call_count == 2  # Interest and GST

    # Verify interest transaction
    call1 = mock_create_transaction.call_args_list[0]
    assert call1.kwargs["tx_type"] == TransactionType.EMI_INTEREST
    assert call1.kwargs["amount_paise"] == 100_00

    # Verify GST transaction
    call2 = mock_create_transaction.call_args_list[1]
    assert call2.kwargs["tx_type"] == TransactionType.EMI_GST
    assert call2.kwargs["amount_paise"] == 18_00


@pytest.mark.asyncio
async def test_pay_emi_installment_already_paid() -> None:
    org_id = uuid4()
    card_id = uuid4()
    plan_id = uuid4()
    inst_id = uuid4()
    user_id = uuid4()

    plan = EmiPlan(
        id=plan_id,
        organization_id=org_id,
        credit_card_id=card_id,
        principal_paise=10000_00,
        interest_rate_bps=1200,
        tenure_months=3,
        status=EmiPlanStatus.ACTIVE,
    )

    inst = EmiInstallment(
        id=inst_id,
        plan_id=plan_id,
        sequence_number=1,
        due_date=date(2026, 2, 1),
        principal_paise=3300_00,
        interest_paise=100_00,
        gst_paise=18_00,
        fees_paise=0,
        total_paise=3418_00,
        status=EmiInstallmentStatus.PAID,
    )

    db = _RecordingSession([
        [(inst, plan)],
    ])

    with pytest.raises(AppError) as exc:
        await emi_service.pay_emi_installment(
            db,  # type: ignore[arg-type]
            organization_id=org_id,
            user_id=user_id,
            installment_id=inst_id,
        )

    assert "already paid" in str(exc.value)
