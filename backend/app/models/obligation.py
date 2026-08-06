"""Debts and loans."""

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ObligationStatus, ObligationType


class Obligation(Base):
    __tablename__ = "obligations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    counterparty_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    type: Mapped[ObligationType] = mapped_column(
        SAEnum(
            ObligationType,
            name="obligation_type",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )

    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="INR", server_default="INR"
    )

    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[ObligationStatus] = mapped_column(
        SAEnum(
            ObligationStatus,
            name="obligation_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=ObligationStatus.ACTIVE,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
