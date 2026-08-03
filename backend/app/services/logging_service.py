"""Persist activity, error, and API request logs."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ActivityAction, ErrorSeverity
from app.models.logging import ActivityLog, ApiRequestLog, ErrorLog


async def log_activity(
    session: AsyncSession,
    *,
    action: ActivityAction,
    summary: str,
    actor_user_id: UUID | None = None,
    organization_id: UUID | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    commit: bool = False,
) -> ActivityLog:
    row = ActivityLog(
        actor_user_id=actor_user_id,
        organization_id=organization_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        summary=summary[:500],
        metadata_json=metadata,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.add(row)
    if commit:
        await session.commit()
    else:
        await session.flush()
    return row


async def log_error(
    session: AsyncSession,
    *,
    message: str,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    actor_user_id: UUID | None = None,
    organization_id: UUID | None = None,
    error_code: str | None = None,
    exception_type: str | None = None,
    stack_trace: str | None = None,
    path: str | None = None,
    method: str | None = None,
    request_id: str | None = None,
    context: dict[str, Any] | None = None,
    commit: bool = True,
) -> ErrorLog:
    row = ErrorLog(
        actor_user_id=actor_user_id,
        organization_id=organization_id,
        severity=severity,
        error_code=error_code,
        message=message,
        exception_type=exception_type,
        stack_trace=stack_trace,
        path=path,
        method=method,
        request_id=request_id,
        context=context,
    )
    session.add(row)
    if commit:
        await session.commit()
    else:
        await session.flush()
    return row


async def log_api_request(
    session: AsyncSession,
    *,
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    duration_ms: int,
    actor_user_id: UUID | None = None,
    query_string: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_body: dict[str, Any] | None = None,
    error_message: str | None = None,
    commit: bool = True,
) -> ApiRequestLog:
    row = ApiRequestLog(
        request_id=request_id,
        actor_user_id=actor_user_id,
        method=method,
        path=path[:500],
        query_string=query_string,
        status_code=status_code,
        duration_ms=duration_ms,
        ip_address=ip_address,
        user_agent=user_agent,
        request_body=request_body,
        error_message=error_message,
    )
    session.add(row)
    if commit:
        await session.commit()
    else:
        await session.flush()
    return row
