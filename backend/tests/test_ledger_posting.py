"""Unit tests for posted-only ledger contribution math."""

import pytest

from app.domain.ledger import card_contribution_paise, contact_contribution_paise
from app.models.enums import PostingStatus, TransactionType


def test_draft_excluded_from_card_contribution() -> None:
    assert (
        card_contribution_paise(
            tx_type=TransactionType.PURCHASE,
            amount_paise=50_00,
            posting_status=PostingStatus.DRAFT,
        )
        == 0
    )


def test_posted_purchase_increases_card() -> None:
    assert (
        card_contribution_paise(
            tx_type=TransactionType.PURCHASE,
            amount_paise=100_00,
            posting_status=PostingStatus.POSTED,
        )
        == 100_00
    )


def test_draft_excluded_from_contact_contribution() -> None:
    assert (
        contact_contribution_paise(
            tx_type=TransactionType.PURCHASE,
            amount_paise=80_00,
            posting_status=PostingStatus.DRAFT,
            contact_id_present=True,
        )
        == 0
    )


def test_contact_contribution_requires_contact() -> None:
    assert (
        contact_contribution_paise(
            tx_type=TransactionType.PURCHASE,
            amount_paise=80_00,
            posting_status=PostingStatus.POSTED,
            contact_id_present=False,
        )
        == 0
    )


def test_reversal_negates_purchase_on_card() -> None:
    assert (
        card_contribution_paise(
            tx_type=TransactionType.REVERSAL,
            amount_paise=250_00,
            posting_status=PostingStatus.POSTED,
            original_type=TransactionType.PURCHASE,
        )
        == -250_00
    )


def test_reversal_of_purchase_nets_zero_outstanding() -> None:
    """T2: Posted purchase 250_00 + reversal → net card outstanding 0."""
    amount = 250_00
    purchase = card_contribution_paise(
        tx_type=TransactionType.PURCHASE,
        amount_paise=amount,
        posting_status=PostingStatus.POSTED,
    )
    reversal = card_contribution_paise(
        tx_type=TransactionType.REVERSAL,
        amount_paise=amount,
        posting_status=PostingStatus.POSTED,
        original_type=TransactionType.PURCHASE,
    )
    assert purchase == amount
    assert reversal == -amount
    assert purchase + reversal == 0


def test_reversal_negates_refund_on_card() -> None:
    assert (
        card_contribution_paise(
            tx_type=TransactionType.REVERSAL,
            amount_paise=40_00,
            posting_status=PostingStatus.POSTED,
            original_type=TransactionType.REFUND,
        )
        == 40_00
    )


def test_reversal_of_refund_restores_outstanding() -> None:
    """T2: Posted refund 40_00 then reverse → outstanding returns +40_00 net from pair."""
    amount = 40_00
    refund = card_contribution_paise(
        tx_type=TransactionType.REFUND,
        amount_paise=amount,
        posting_status=PostingStatus.POSTED,
    )
    reversal = card_contribution_paise(
        tx_type=TransactionType.REVERSAL,
        amount_paise=amount,
        posting_status=PostingStatus.POSTED,
        original_type=TransactionType.REFUND,
    )
    assert refund == -amount
    assert reversal == amount
    assert refund + reversal == 0


def test_reversal_negates_purchase_on_contact() -> None:
    """T2: Contact-attributed purchase reversed → contact contribution nets to 0."""
    amount = 90_00
    spend = contact_contribution_paise(
        tx_type=TransactionType.PURCHASE,
        amount_paise=amount,
        posting_status=PostingStatus.POSTED,
        contact_id_present=True,
    )
    reversal = contact_contribution_paise(
        tx_type=TransactionType.REVERSAL,
        amount_paise=amount,
        posting_status=PostingStatus.POSTED,
        contact_id_present=True,
        original_type=TransactionType.PURCHASE,
    )
    assert spend + reversal == 0


def test_adjustment_positive_delta_increases_card() -> None:
    """T3: +delta → outstanding +amount; delta_sign=1 semantics."""
    assert (
        card_contribution_paise(
            tx_type=TransactionType.ADJUSTMENT,
            amount_paise=150_00,
            posting_status=PostingStatus.POSTED,
            delta_sign=1,
        )
        == 150_00
    )


def test_adjustment_negative_delta_decreases_card() -> None:
    """T3: −delta → outstanding −amount; delta_sign=-1 semantics."""
    assert (
        card_contribution_paise(
            tx_type=TransactionType.ADJUSTMENT,
            amount_paise=75_00,
            posting_status=PostingStatus.POSTED,
            delta_sign=-1,
        )
        == -75_00
    )


def test_adjustment_with_contact_moves_card_and_contact() -> None:
    """T3: adjustment + contact_id → both card and contact move by signed delta."""
    amount = 20_00
    card = card_contribution_paise(
        tx_type=TransactionType.ADJUSTMENT,
        amount_paise=amount,
        posting_status=PostingStatus.POSTED,
        delta_sign=1,
    )
    contact = contact_contribution_paise(
        tx_type=TransactionType.ADJUSTMENT,
        amount_paise=amount,
        posting_status=PostingStatus.POSTED,
        contact_id_present=True,
        delta_sign=1,
    )
    assert card == amount
    assert contact == amount

    neg_card = card_contribution_paise(
        tx_type=TransactionType.ADJUSTMENT,
        amount_paise=amount,
        posting_status=PostingStatus.POSTED,
        delta_sign=-1,
    )
    neg_contact = contact_contribution_paise(
        tx_type=TransactionType.ADJUSTMENT,
        amount_paise=amount,
        posting_status=PostingStatus.POSTED,
        contact_id_present=True,
        delta_sign=-1,
    )
    assert neg_card == -amount
    assert neg_contact == -amount


def test_adjustment_without_contact_skips_contact_balance() -> None:
    assert (
        contact_contribution_paise(
            tx_type=TransactionType.ADJUSTMENT,
            amount_paise=20_00,
            posting_status=PostingStatus.POSTED,
            contact_id_present=False,
            delta_sign=1,
        )
        == 0
    )


def test_draft_adjustment_excluded_from_outstanding() -> None:
    assert (
        card_contribution_paise(
            tx_type=TransactionType.ADJUSTMENT,
            amount_paise=50_00,
            posting_status=PostingStatus.DRAFT,
            delta_sign=1,
        )
        == 0
    )


def test_adjustment_requires_delta_sign() -> None:
    with pytest.raises(ValueError, match="delta_sign"):
        card_contribution_paise(
            tx_type=TransactionType.ADJUSTMENT,
            amount_paise=10_00,
            posting_status=PostingStatus.POSTED,
            delta_sign=None,
        )


def test_posted_only_sum_matches_filter_semantics() -> None:
    """T1: Draft + posted mix — only posted rows affect card outstanding."""
    rows = [
        (TransactionType.PURCHASE, 100_00, PostingStatus.POSTED, None, None),
        (TransactionType.PURCHASE, 50_00, PostingStatus.DRAFT, None, None),
    ]
    total = sum(
        card_contribution_paise(
            tx_type=t,
            amount_paise=amt,
            posting_status=status,
            delta_sign=ds,
            original_type=ot,
        )
        for t, amt, status, ds, ot in rows
    )
    assert total == 100_00


def test_draft_excluded_from_contact_balance_mix() -> None:
    """T1: Posted purchase w/ contact 80_00 + draft 20_00 → contact balance 80_00."""
    rows = [
        (TransactionType.PURCHASE, 80_00, PostingStatus.POSTED),
        (TransactionType.PURCHASE, 20_00, PostingStatus.DRAFT),
    ]
    total = sum(
        contact_contribution_paise(
            tx_type=t,
            amount_paise=amt,
            posting_status=status,
            contact_id_present=True,
        )
        for t, amt, status in rows
    )
    assert total == 80_00


def test_draft_only_org_outstanding_is_zero() -> None:
    """T1: Only draft rows → card and contact outstanding are 0."""
    drafts = [
        (TransactionType.PURCHASE, 100_00),
        (TransactionType.FEE, 25_00),
    ]
    card_total = sum(
        card_contribution_paise(
            tx_type=t,
            amount_paise=amt,
            posting_status=PostingStatus.DRAFT,
        )
        for t, amt in drafts
    )
    contact_total = sum(
        contact_contribution_paise(
            tx_type=t,
            amount_paise=amt,
            posting_status=PostingStatus.DRAFT,
            contact_id_present=True,
        )
        for t, amt in drafts
    )
    assert card_total == 0
    assert contact_total == 0


def test_post_draft_then_included_in_outstanding() -> None:
    """T1: Draft contributes 0; after post, amount enters outstanding."""
    amount = 150_00
    assert (
        card_contribution_paise(
            tx_type=TransactionType.PURCHASE,
            amount_paise=amount,
            posting_status=PostingStatus.DRAFT,
        )
        == 0
    )
    assert (
        card_contribution_paise(
            tx_type=TransactionType.PURCHASE,
            amount_paise=amount,
            posting_status=PostingStatus.POSTED,
        )
        == amount
    )
    assert (
        contact_contribution_paise(
            tx_type=TransactionType.PURCHASE,
            amount_paise=amount,
            posting_status=PostingStatus.DRAFT,
            contact_id_present=True,
        )
        == 0
    )
    assert (
        contact_contribution_paise(
            tx_type=TransactionType.PURCHASE,
            amount_paise=amount,
            posting_status=PostingStatus.POSTED,
            contact_id_present=True,
        )
        == amount
    )
