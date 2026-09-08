import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.transaction import Transaction


class CategoryKind(enum.StrEnum):
    income = "income"
    expense = "expense"


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("id", "org_id", name="uq_categories_id_org"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )

    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[CategoryKind] = mapped_column(Enum(CategoryKind, native_enum=False, length=30))
    color: Mapped[str | None] = mapped_column(String(30))
    icon: Mapped[str | None] = mapped_column(String(50))

    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    org: Mapped["Organization"] = relationship("Organization")
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="category_rel"
    )
