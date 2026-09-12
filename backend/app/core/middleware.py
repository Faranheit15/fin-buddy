"""HTTP middleware: request ID, API request logging, error persistence."""

import asyncio
import time
import traceback

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.request_meta import client_ip, redacted_query_string, request_id
from app.db.session import get_async_session_factory
from app.models.enums import ErrorSeverity
from app.services.logging_service import log_api_request, log_error

logger = get_logger(__name__)

SKIP_PATH_PREFIXES = (
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon",
    "/api/v1/health",
    "/api/v1/ready",
)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = request_id(request)
        request.state.request_id = correlation_id
        start = time.perf_counter()
        status_code = 500
        error_message: str | None = None
        response: Response | None = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-Id"] = correlation_id
            return response
        except Exception as exc:
            error_message = f"Unhandled {type(exc).__name__}"
            await self._persist_error(request, correlation_id, exc)
            raise
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)
            # Don't block the HTTP response on request-log writes.
            asyncio.create_task(
                self._persist_request_log(
                    request=request,
                    request_id=correlation_id,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    error_message=error_message,
                )
            )

    async def _persist_request_log(
        self,
        *,
        request: Request,
        request_id: str,
        status_code: int,
        duration_ms: int,
        error_message: str | None,
    ) -> None:
        settings = get_settings()
        if not settings.log_api_requests or not settings.database_configured:
            return
        if any(request.url.path.startswith(p) for p in SKIP_PATH_PREFIXES):
            return
        # Avoid logging health spam at info volume — still store for admin
        try:
            factory = get_async_session_factory()
        except RuntimeError:
            return

        ip = client_ip(request)

        try:
            async with factory() as session:
                await log_api_request(
                    session,
                    request_id=request_id,
                    method=request.method,
                    path=request.url.path,
                    query_string=redacted_query_string(request),
                    status_code=status_code,
                    duration_ms=duration_ms,
                    ip_address=ip,
                    user_agent=request.headers.get("user-agent"),
                    error_message=error_message,
                    commit=True,
                )
        except Exception:
            logger.exception("api_request_log_failed", request_id=request_id)

    async def _persist_error(self, request: Request, request_id: str, exc: Exception) -> None:
        settings = get_settings()
        if not settings.database_configured:
            return
        try:
            factory = get_async_session_factory()
        except RuntimeError:
            return
        try:
            async with factory() as session:
                await log_error(
                    session,
                    message=f"Unhandled {type(exc).__name__}",
                    severity=ErrorSeverity.ERROR,
                    exception_type=type(exc).__name__,
                    stack_trace="".join(traceback.format_tb(exc.__traceback__)),
                    path=request.url.path,
                    method=request.method,
                    request_id=request_id,
                    commit=True,
                )
        except Exception:
            logger.exception("error_log_failed", request_id=request_id)
