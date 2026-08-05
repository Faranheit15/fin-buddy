import pytest
from uuid import uuid4
from datetime import datetime, UTC

from app.models.enums import PostingStatus, TransactionType, AccountKind
from app.services import transaction_service
from app.domain.ledger import CARD_EFFECT, ASSET_EFFECT
from tests.test_transaction_api_posting import _RecordingSession

@pytest.mark.asyncio
async def test_transfer_creates_linked_legs() -> None:
    org_id = uuid4()
    user_id = uuid4()
    from_account_id = uuid4()
    to_account_id = uuid4()
    amount = 500_00
    
    class FakeAccount:
        def __init__(self, id, kind=AccountKind.BANK):
            self.id = id
            self.kind = kind
            self.credit_card_id = None
            self.currency = "INR"
            
    # Needs accounts mocked because _resolve_transaction_account is called.
    # Actually create_transfer calls _resolve_transaction_account twice, so we mock 2 FakeAccounts.
    db = _RecordingSession([FakeAccount(from_account_id), FakeAccount(to_account_id)])
    
    out_tx, in_tx = await transaction_service.create_transfer(
        db, # type: ignore[arg-type]
        organization_id=org_id,
        user_id=user_id,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        amount_paise=amount,
        occurred_at=datetime.now(UTC)
    )
    
    assert out_tx.type == TransactionType.TRANSFER_OUT
    assert out_tx.amount_paise == amount
    assert out_tx.account_id == from_account_id
    assert out_tx.transfer_group_id is not None
    
    assert in_tx.type == TransactionType.TRANSFER_IN
    assert in_tx.amount_paise == amount
    assert in_tx.account_id == to_account_id
    assert in_tx.transfer_group_id == out_tx.transfer_group_id
    
    # Verify excluded from income/expense explicitly in service (just verify types here)
    # But it does affect assets/cards correctly
    assert CARD_EFFECT[out_tx.type] == 1
    assert CARD_EFFECT[in_tx.type] == -1
    assert ASSET_EFFECT[out_tx.type] == -1
    assert ASSET_EFFECT[in_tx.type] == 1
