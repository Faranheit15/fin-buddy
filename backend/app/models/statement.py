"""Credit card statements and import review lines."""

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import LineReviewStatus, StatementStatus, TransactionType


class Statement(Base):
    __tablename__ = "statements"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    credit_card_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("credit_cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    statement_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    pdf_storage_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[StatementStatus] = mapped_column(
        SAEnum(
            StatementStatus,
            name="statement_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=StatementStatus.UPLOADED,
        server_default=StatementStatus.UPLOADED.value,
    )
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)
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


class StatementLineCandidate(Base):
    __tablename__ = "statement_line_candidates"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    statement_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("statements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_payload: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    merchant: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount_paise: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    proposed_type: Mapped[TransactionType | None] = mapped_column(
        SAEnum(
            TransactionType,
            name="transaction_type",
            values_callable=lambda x: [e.value for e in x],
            create_constraint=False,
            create_type=False,
        ),
        nullable=True,
    )
    proposed_contact_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    review_status: Mapped[LineReviewStatus] = mapped_column(
        SAEnum(
            LineReviewStatus,
            name="line_review_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=LineReviewStatus.PENDING,
        server_default=LineReviewStatus.PENDING.value,
    )
    committed_transaction_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
