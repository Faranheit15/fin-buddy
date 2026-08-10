"""Shared, privacy-preserving rate-limit windows stored in Supabase Postgres."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RateLimitWindow(Base):
    """Fixed-window counter keyed by a SHA-256 digest, never a raw client address."""

    __tablename__ = "rate_limit_windows"

    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    bucket: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
