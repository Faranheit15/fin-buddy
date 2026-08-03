"""Credit card inventory and billing configuration."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import CardNetwork, CardStatus, DueRuleType


class CreditCard(Base):
    __tablename__ = "credit_cards"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nickname: Mapped[str] = mapped_column(String(120), nullable=False)
    issuer: Mapped[str] = mapped_column(String(120), nullable=False)
    network: Mapped[CardNetwork] = mapped_column(
        SAEnum(CardNetwork, name="card_network", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=CardNetwork.OTHER,
    )
    last_four: Mapped[str] = mapped_column(String(4), nullable=False)
    credit_limit_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR", server_default="INR")
    statement_day: Mapped[int] = mapped_column(Integer, nullable=False)
    due_rule_type: Mapped[DueRuleType] = mapped_column(
        SAEnum(DueRuleType, name="due_rule_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    due_rule_value: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[CardStatus] = mapped_column(
        SAEnum(CardStatus, name="card_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=CardStatus.ACTIVE,
        server_default=CardStatus.ACTIVE.value,
    )
    held_by_contact_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
