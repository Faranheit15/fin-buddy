"""Database engine and session factories."""

from collections.abc import AsyncGenerator, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings

_async_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None
_sync_engine = None
_sync_session_factory: sessionmaker[Session] | None = None


def init_db(settings: Settings | None = None) -> None:
    """Create engines and session factories (idempotent)."""
    global _async_engine, _async_session_factory, _sync_engine, _sync_session_factory

    settings = settings or get_settings()
    if not settings.database_configured:
        return

    if _async_engine is None:
        db_url = settings.async_database_url()
        connect_args: dict[str, object] = {
            "timeout": 5.0,
        }
        if "pooler.supabase.com" in db_url or ":6543" in db_url:
            connect_args["statement_cache_size"] = 0

        _async_engine = create_async_engine(
            db_url,
            echo=settings.database_echo,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_recycle=1800,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        _async_session_factory = async_sessionmaker(
            _async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    if _sync_engine is None:
        _sync_engine = create_engine(
            settings.sync_database_url(),
            echo=settings.database_echo,
            pool_pre_ping=True,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
        )
        _sync_session_factory = sessionmaker(
            _sync_engine,
            expire_on_commit=False,
            autoflush=False,
        )


async def dispose_db() -> None:
    """Dispose engines on shutdown."""
    global _async_engine, _async_session_factory, _sync_engine, _sync_session_factory
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
        _async_session_factory = None
    if _sync_engine is not None:
        _sync_engine.dispose()
        _sync_engine = None
        _sync_session_factory = None


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    if _async_session_factory is None:
        init_db()
    if _async_session_factory is None:
        raise RuntimeError("Database is not configured (set DATABASE_URL)")
    return _async_session_factory


def get_sync_session_factory() -> sessionmaker[Session]:
    if _sync_session_factory is None:
        init_db()
    if _sync_session_factory is None:
        raise RuntimeError("Database is not configured (set DATABASE_URL)")
    return _sync_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async session. Callers commit explicitly."""
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@contextmanager
def sync_session_scope() -> Generator[Session, None, None]:
    """Sync session context for migrations/seeds/bootstrap."""
    factory = get_sync_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
