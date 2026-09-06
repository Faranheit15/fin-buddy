"""Health and readiness endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.session import get_async_session_factory
from app.schemas.health import HealthResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/ready", response_model=HealthResponse)
async def ready(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    status: str = "ok"
    if settings.database_configured:
        try:
            factory = get_async_session_factory()
            async with factory() as session:
                await session.execute(text("SELECT 1"))
        except Exception as exc:
            logger.warning("Readiness probe database ping failed", exc_info=exc)
            status = "degraded"
    elif settings.environment not in ("test", "development"):
        # Production/staging without DB is not ready
        status = "degraded"

    return HealthResponse(
        status=status,  # type: ignore[arg-type]
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
