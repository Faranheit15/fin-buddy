"""Account deletion tombstone model.

Prevents deleted accounts from being resurrected by stale JWTs or refresh tokens,
and tracks provider-level deletion status for resilient retries.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DeletedAccount(Base):
    __tablename__ = "deleted_accounts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    provider_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
