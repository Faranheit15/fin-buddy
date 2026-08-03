"""Admin panel schemas."""

from datetime import datetime
from uuid import UUID

from app.models.enums import ActivityAction, ErrorSeverity, PlatformRole
from app.schemas.common import ORMModel


class ActivityLogResponse(ORMModel):
    id: UUID
    actor_user_id: UUID | None
    organization_id: UUID | None
    action: ActivityAction
    resource_type: str | None
    resource_id: str | None
    summary: str
    metadata: dict[str, object] | None = None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ErrorLogResponse(ORMModel):
    id: UUID
    actor_user_id: UUID | None
    organization_id: UUID | None
    severity: ErrorSeverity
    error_code: str | None
    message: str
    exception_type: str | None
    stack_trace: str | None
    path: str | None
    method: str | None
    request_id: str | None
    context: dict[str, object] | None
    created_at: datetime


class ApiRequestLogResponse(ORMModel):
    id: UUID
    request_id: str
    actor_user_id: UUID | None
    method: str
    path: str
    query_string: str | None
    status_code: int
    duration_ms: int
    ip_address: str | None
    user_agent: str | None
    error_message: str | None
    created_at: datetime


class AdminUserResponse(ORMModel):
    id: UUID
    email: str | None
    phone: str | None
    display_name: str | None
    platform_role: PlatformRole
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime
