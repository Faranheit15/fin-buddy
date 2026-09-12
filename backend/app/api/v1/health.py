"""Health and readiness endpoints."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.session import get_async_session_factory
from app.schemas.health import HealthResponse

logger = get_logger(__name__)
router = APIRouter()

READINESS_TIMEOUT_SECONDS = 2.5


@router.get("/health", response_model=HealthResponse)
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/ready", response_model=HealthResponse)
async def ready(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    status_str: str = "ok"
    if settings.database_configured:
        try:
            async with asyncio.timeout(READINESS_TIMEOUT_SECONDS):
                factory = get_async_session_factory()
                async with factory() as session:
                    await session.execute(text("SELECT 1"))
        except TimeoutError:
            logger.warning(
                "Readiness probe database ping timed out after %.1fs",
                READINESS_TIMEOUT_SECONDS,
            )
            status_str = "degraded"
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        except Exception:
            logger.warning("Readiness probe database ping failed")
            status_str = "degraded"
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif settings.environment not in ("test", "development"):
        # Production/staging without DB is not ready
        status_str = "degraded"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=status_str,  # type: ignore[arg-type]
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
