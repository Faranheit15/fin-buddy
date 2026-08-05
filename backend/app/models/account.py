"""Unified money accounts (bank, cash, wallet, credit card)."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AccountKind


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint(
            "(kind = 'credit_card' AND credit_card_id IS NOT NULL) OR "
            "(kind <> 'credit_card' AND credit_card_id IS NULL)",
            name="ck_accounts_kind_card",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[AccountKind] = mapped_column(
        SAEnum(
            AccountKind,
            name="account_kind",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    institution: Mapped[str | None] = mapped_column(String(120), nullable=True)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="INR", server_default="INR"
    )
    credit_card_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("credit_cards.id", ondelete="RESTRICT"),
        nullable=True,
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
