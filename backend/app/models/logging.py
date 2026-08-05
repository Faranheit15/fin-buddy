"""Activity, error, and API request logs for the admin panel."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ActivityAction, ErrorSeverity


class ActivityLog(Base):
    """User / admin actions for product analytics and admin audit."""

    __tablename__ = "activity_logs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    organization_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[ActivityAction] = mapped_column(
        SAEnum(
            ActivityAction,
            name="activity_action",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
    )
    resource_type: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    metadata_json: Mapped[dict[str, object] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class ErrorLog(Base):
    """Captured application errors for admin debugging."""

    __tablename__ = "error_logs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    organization_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    severity: Mapped[ErrorSeverity] = mapped_column(
        SAEnum(
            ErrorSeverity,
            name="error_severity",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=ErrorSeverity.ERROR,
        index=True,
    )
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    exception_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    stack_trace: Mapped[str | None] = mapped_column(Text, nullable=True)
    path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    method: Mapped[str | None] = mapped_column(String(16), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    context: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class ApiRequestLog(Base):
    """HTTP request log for admin observability."""

    __tablename__ = "api_request_logs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    query_string: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_body: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class SeedHistory(Base):
    """Tracks which seeders have been applied (idempotent seeds)."""

    __tablename__ = "seed_history"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    seed_name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
