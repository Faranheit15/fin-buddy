"""Run Alembic migrations programmatically on startup."""

from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.logging import get_logger

logger = get_logger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def run_migrations() -> None:
    """Upgrade database schema to head."""
    ini_path = BACKEND_ROOT / "alembic.ini"
    if not ini_path.exists():
        raise FileNotFoundError(f"alembic.ini not found at {ini_path}")

    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    logger.info("alembic_upgrade_start", path=str(ini_path))
    command.upgrade(cfg, "head")
    logger.info("alembic_upgrade_complete")
