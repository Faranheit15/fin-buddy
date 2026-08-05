"""Pure ledger contribution math — integer paise only."""

from __future__ import annotations

from app.models.enums import PostingStatus, TransactionType

# Effects on card outstanding (issuer liability)
CARD_EFFECT: dict[TransactionType, int] = {
    TransactionType.PURCHASE: 1,
    TransactionType.FEE: 1,
    TransactionType.INTEREST: 1,
    TransactionType.OPENING_BALANCE: 1,
    TransactionType.REFUND: -1,
    TransactionType.PAYMENT_TO_ISSUER: -1,
}

# Effects on contact balance (what they owe the card owner)
CONTACT_EFFECT: dict[TransactionType, int] = {
    TransactionType.PURCHASE: 1,
    TransactionType.FEE: 1,
    TransactionType.INTEREST: 1,
    TransactionType.OPENING_BALANCE: 0,  # typically self
    TransactionType.REFUND: -1,
    TransactionType.PAYMENT_TO_ISSUER: 0,
}


def card_contribution_paise(
    *,
    tx_type: TransactionType,
    amount_paise: int,
    posting_status: PostingStatus,
    delta_sign: int | None = None,
    original_type: TransactionType | None = None,
) -> int:
    """Signed paise effect on card outstanding; drafts contribute 0."""
    if posting_status != PostingStatus.POSTED:
        return 0
    if amount_paise < 0:
        raise ValueError("amount_paise must be >= 0")
    if tx_type == TransactionType.ADJUSTMENT:
        if delta_sign not in (-1, 1):
            raise ValueError("adjustment requires delta_sign of -1 or 1")
        return delta_sign * amount_paise
    if tx_type == TransactionType.REVERSAL:
        if original_type is None:
            raise ValueError("reversal requires original_type")
        mult = CARD_EFFECT.get(original_type, 0)
        return -mult * amount_paise
    return CARD_EFFECT.get(tx_type, 0) * amount_paise


def contact_contribution_paise(
    *,
    tx_type: TransactionType,
    amount_paise: int,
    posting_status: PostingStatus,
    contact_id_present: bool,
    delta_sign: int | None = None,
    original_type: TransactionType | None = None,
) -> int:
    """Signed paise effect on contact balance; drafts / no contact contribute 0."""
    if posting_status != PostingStatus.POSTED or not contact_id_present:
        return 0
    if amount_paise < 0:
        raise ValueError("amount_paise must be >= 0")
    if tx_type == TransactionType.ADJUSTMENT:
        if delta_sign not in (-1, 1):
            raise ValueError("adjustment requires delta_sign of -1 or 1")
        return delta_sign * amount_paise
    if tx_type == TransactionType.REVERSAL:
        if original_type is None:
            raise ValueError("reversal requires original_type")
        mult = CONTACT_EFFECT.get(original_type, 0)
        return -mult * amount_paise
    return CONTACT_EFFECT.get(tx_type, 0) * amount_paise
