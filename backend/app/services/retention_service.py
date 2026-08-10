"""Retention controls for sensitive operational logs."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logging import ActivityLog, ApiRequestLog, ErrorLog


async def purge_operational_logs(session: AsyncSession, *, retention_days: int) -> None:
    """Remove expired request, activity, and error logs in one transaction."""
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    for model in (ActivityLog, ApiRequestLog, ErrorLog):
        await session.execute(delete(model).where(model.created_at < cutoff))
