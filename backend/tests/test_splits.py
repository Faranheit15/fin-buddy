from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import AppError
from app.models.enums import PostingStatus
from app.services import transaction_service
from tests.test_transaction_api_posting import _posted_purchase, _RecordingSession


@pytest.mark.asyncio
async def test_replace_transaction_splits_valid() -> None:
    tx = _posted_purchase(posting_status=PostingStatus.DRAFT)
    cat1_id = uuid4()
    cat2_id = uuid4()
    c1 = SimpleNamespace(id=cat1_id, org_id=tx.organization_id)
    c2 = SimpleNamespace(id=cat2_id, org_id=tx.organization_id)
    db = _RecordingSession([tx, None, c1, c2])

    splits_data = [
        {"amount_paise": 100_00, "category_id": cat1_id},
        {"amount_paise": 150_00, "category_id": cat2_id},
    ]

    await transaction_service.replace_transaction_splits(
        db,  # type: ignore[arg-type]
        organization_id=tx.organization_id,
        user_id=uuid4(),
        transaction_id=tx.id,
        splits_data=splits_data,
    )

    # We should have flushed.
    assert db.flush_count >= 1


@pytest.mark.asyncio
async def test_replace_transaction_splits_invalid_sum() -> None:
    tx = _posted_purchase(amount_paise=250_00, posting_status=PostingStatus.DRAFT)
    db = _RecordingSession([tx])

    splits_data = [
        {"amount_paise": 100_00, "category_id": uuid4()},
        {"amount_paise": 100_00, "category_id": uuid4()},  # Sum is 200_00, not 250_00
    ]

    with pytest.raises(AppError) as exc:
        await transaction_service.replace_transaction_splits(
            db,  # type: ignore[arg-type]
            organization_id=tx.organization_id,
            user_id=uuid4(),
            transaction_id=tx.id,
            splits_data=splits_data,
        )
    assert exc.value.code == "invalid_splits_sum"
