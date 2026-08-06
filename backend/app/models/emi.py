"""Card EMI models."""

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import EmiInstallmentStatus, EmiPlanStatus


class EmiPlan(Base):
    __tablename__ = "emi_plans"

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
    reference_transaction_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    principal_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    interest_rate_bps: Mapped[int] = mapped_column(Integer, nullable=False)  # e.g., 1500 for 15.00%
    tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    
    status: Mapped[EmiPlanStatus] = mapped_column(
        SAEnum(
            EmiPlanStatus,
            name="emi_plan_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=EmiPlanStatus.ACTIVE,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    
    installments: Mapped[list["EmiInstallment"]] = relationship(
        "EmiInstallment", back_populates="plan", cascade="all, delete-orphan"
    )


class EmiInstallment(Base):
    __tablename__ = "emi_installments"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("emi_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    principal_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    interest_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fees_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    gst_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    status: Mapped[EmiInstallmentStatus] = mapped_column(
        SAEnum(
            EmiInstallmentStatus,
            name="emi_installment_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=EmiInstallmentStatus.PENDING,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    
    plan: Mapped["EmiPlan"] = relationship("EmiPlan", back_populates="installments")
