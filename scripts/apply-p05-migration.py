#!/usr/bin/env python3
"""Explicitly apply Alembic migrations to head on target Supabase database.

Reads DATABASE_URL from backend/.env or environment.
Never enables AUTO_MIGRATE in production configuration.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from alembic import command
from alembic.config import Config
from app.core.config import get_settings


def apply_migration() -> bool:
    settings = get_settings()
    if not settings.database_configured or not settings.database_url:
        print("ERROR: DATABASE_URL is not configured in backend/.env or environment.")
        print("Add the Supabase Session Pooler URI to backend/.env (gitignored) to run the migration.")
        return False

    ini_path = BACKEND_DIR / "alembic.ini"
    if not ini_path.exists():
        print(f"ERROR: alembic.ini not found at {ini_path}")
        return False

    print("Running explicit release migration gate to head...")
    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    try:
        command.upgrade(cfg, "head")
        print("Explicit migration to head completed successfully.")
        return True
    except Exception as e:
        print(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
