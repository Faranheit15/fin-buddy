"""Idempotent seed runner using seed_history table."""

from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import sync_session_scope
from app.models.logging import SeedHistory
from app.seeders import SEEDERS

logger = get_logger(__name__)


def _already_applied(session: Session, name: str) -> bool:
    return (
        session.execute(select(SeedHistory.id).where(SeedHistory.seed_name == name)).scalar_one_or_none()
        is not None
    )


def run_seeds(force: bool = False) -> list[str]:
    """
    Apply pending seeders.

    Each seeder is a (name, callable) that receives a Session.
    """
    applied: list[str] = []
    with sync_session_scope() as session:
        for name, fn in SEEDERS:
            if not force and _already_applied(session, name):
                logger.info("seed_skip", seed=name)
                continue
            logger.info("seed_apply", seed=name)
            fn(session)
            if not _already_applied(session, name):
                session.add(SeedHistory(seed_name=name, notes=f"Applied by bootstrap: {name}"))
            session.flush()
            applied.append(name)
        session.commit()
    logger.info("seeds_complete", applied=applied)
    return applied


def register_seeder(name: str, fn: Callable[[Session], None]) -> None:
    """Runtime registration helper (tests)."""
    SEEDERS.append((name, fn))
