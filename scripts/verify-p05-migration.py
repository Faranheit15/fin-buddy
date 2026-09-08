#!/usr/bin/env python3
"""Verify US-P05 migration 20260908_0017 on Supabase Postgres.

Runs non-secret verification SQL:
1. public.alembic_version = 20260908_0017
2. public.idempotency_records exists
3. P05 unique indexes and constraints exist
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so app modules load
BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, text
from app.core.config import get_settings


def verify() -> bool:
    settings = get_settings()
    if not settings.database_configured or not settings.database_url:
        print("ERROR: DATABASE_URL is not configured in backend/.env or environment.")
        print("Add the Supabase Session Pooler URI to backend/.env (gitignored) to run verification.")
        return False

    print("Connecting to Supabase PostgreSQL database...")
    engine = create_engine(settings.sync_database_url(), pool_pre_ping=True)

    all_passed = True
    with engine.connect() as conn:
        # 1. alembic_version
        version = conn.execute(text("SELECT version_num FROM alembic_version;")).scalar()
        print(f"\n1. Alembic Version Check:")
        print(f"   Current revision: {version}")
        if version == "20260908_0017":
            print("   Status: PASS (Matches 20260908_0017)")
        else:
            print("   Status: FAIL (Expected 20260908_0017)")
            all_passed = False

        # 2. idempotency_records table
        table_exists = conn.execute(
            text(
                "SELECT EXISTS ("
                "   SELECT 1 FROM information_schema.tables "
                "   WHERE table_schema = 'public' AND table_name = 'idempotency_records'"
                ");"
            )
        ).scalar()
        print(f"\n2. Table Existence Check:")
        print(f"   idempotency_records exists: {table_exists}")
        if table_exists:
            print("   Status: PASS")
        else:
            print("   Status: FAIL")
            all_passed = False

        # 3. P05 indexes & unique constraints
        indexes_query = conn.execute(
            text(
                "SELECT indexname FROM pg_indexes "
                "WHERE schemaname = 'public' "
                "  AND indexname IN ("
                "    'uq_transactions_reverses_id',"
                "    'uq_statement_lines_committed_tx',"
                "    'uq_emi_installments_plan_seq',"
                "    'uq_settlements_id_org',"
                "    'uq_idempotency_org_key'"
                "  ) "
                "ORDER BY indexname;"
            )
        ).fetchall()
        found_indexes = [row[0] for row in indexes_query]
        print(f"\n3. P05 Constraints and Indexes Check:")
        expected_indexes = [
            "uq_emi_installments_plan_seq",
            "uq_idempotency_org_key",
            "uq_settlements_id_org",
            "uq_statement_lines_committed_tx",
            "uq_transactions_reverses_id",
        ]
        for idx in expected_indexes:
            present = idx in found_indexes
            print(f"   - {idx}: {'FOUND' if present else 'MISSING'}")
            if not present:
                all_passed = False

    return all_passed


if __name__ == "__main__":
    success = verify()
    sys.exit(0 if success else 1)
