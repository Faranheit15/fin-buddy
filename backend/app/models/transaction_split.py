import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Integer, ARRAY, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.category import Category


class TransactionSplit(Base):
    __tablename__ = "transaction_splits"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    transaction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transactions.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), index=True)
    
    amount_paise: Mapped[int] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(String(500))
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text))

    # Relationships
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="splits")
    category: Mapped[Optional["Category"]] = relationship("Category")
