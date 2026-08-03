"""Startup bootstrap: migrations + seeds."""

from app.bootstrap.migrate import run_migrations
from app.bootstrap.seed import run_seeds
from app.core.config import Settings
from app.core.logging import get_logger
from app.db.session import init_db

logger = get_logger(__name__)


def bootstrap_database(settings: Settings) -> None:
    """
    Initialize DB engines, run Alembic to head, then apply pending seeds.

    Controlled by AUTO_MIGRATE / AUTO_SEED settings.
    """
    if not settings.database_configured:
        logger.warning("bootstrap_skipped", reason="DATABASE_URL not set")
        return

    init_db(settings)

    if settings.auto_migrate:
        try:
            run_migrations()
        except Exception:
            logger.exception("bootstrap_migrate_failed")
            raise
    else:
        logger.info("bootstrap_migrate_disabled")

    if settings.auto_seed:
        try:
            run_seeds()
        except Exception:
            logger.exception("bootstrap_seed_failed")
            raise
    else:
        logger.info("bootstrap_seed_disabled")
