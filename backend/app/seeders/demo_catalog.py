"""
Baseline seed data that does not depend on a real user.

Reserved for reference metadata. User/org data is created on first auth bootstrap.
"""

from sqlalchemy.orm import Session

from app.core.logging import get_logger

logger = get_logger(__name__)


def seed_demo_catalog_metadata(session: Session) -> None:
    """
    Placeholder / no-op-safe seed that validates the seed pipeline.

    Extend later with transaction categories, issuer list, etc. if stored as tables.
    """
    logger.info("seed_demo_catalog_metadata_ok")
    # Intentionally no rows required — presence in seed_history is the contract.
    _ = session
