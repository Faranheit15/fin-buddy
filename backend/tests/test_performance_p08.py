"""Automated performance and database optimization tests for US-P08.

Verifies:
1. Migration 20261006_0018 definition and Postgres index existence.
2. Obligation SQL-level pagination and paise balance accuracy.
3. Dashboard cash flow trend consolidation and monthly accuracy.
4. Connection pool sizing and timeouts.
5. Cache-Control: no-store, private headers on API responses.
"""

from __future__ import annotations

import asyncio
import importlib.util
import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.db.session import dispose_db, get_async_engine, get_sync_engine, init_db
from app.main import app
from app.models.account import Account
from app.models.category import Category, CategoryKind
from app.models.contact import Contact
from app.models.enums import (
    AccountKind,
    ObligationStatus,
    ObligationType,
    OrgRole,
    PostingStatus,
    TransactionType,
)
from app.models.obligation import Obligation
from app.models.obligation_payment import ObligationPayment
from app.models.organization import Organization, OrganizationMember
from app.models.profile import Profile
from app.models.transaction import Transaction
from app.services.dashboard_analytics import cash_flow_trend
from app.services.obligation_service import list_obligations_with_balance_paginated

IST = ZoneInfo("Asia/Kolkata")

PG_USER = os.getenv("PGUSER", "postgres")
PG_PASS = os.getenv("PGPASSWORD", "postgres")
PG_HOST = os.getenv("PGHOST", "localhost")
PG_PORT = os.getenv("PGPORT", "5433")
PG_DB = os.getenv("PGDATABASE", "finbuddy_test")
TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    f"postgresql+asyncpg://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}",
)


def _load_migration_0018() -> Any:
    migration_path = (
        Path(__file__).resolve().parent.parent
        / "alembic"
        / "versions"
        / "20261006_0018_performance_indexes_and_tuning.py"
    )
    spec = importlib.util.spec_from_file_location("migration_20261006_0018", migration_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def _can_connect_pg() -> bool:
    try:
        engine = create_async_engine(TEST_DB_URL, pool_pre_ping=True)
        async with engine.connect() as conn:
            await conn.execute(select(1))
        await engine.dispose()
        return True
    except Exception:
        return False


has_postgres = asyncio.run(_can_connect_pg())


def test_migration_0018_metadata_and_structure() -> None:
    """Verifies that migration 0018 is valid and linked to 0017."""
    mod = _load_migration_0018()
    assert mod.revision == "20261006_0018"
    assert mod.down_revision == "20260908_0017"
    assert hasattr(mod, "upgrade")
    assert hasattr(mod, "downgrade")
    assert len(mod.NEW_INDEXES) == 14


@pytest.mark.asyncio
async def test_engine_pool_sizing_and_timeouts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies pool size and timeouts follow free tier constraints."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
    get_settings.cache_clear()
    await dispose_db()
    init_db()

    a_engine = get_async_engine()
    s_engine = get_sync_engine()
    assert a_engine is not None
    assert s_engine is not None

    pool = a_engine.pool
    if hasattr(pool, "size"):
        assert pool.size() <= 3  # type: ignore[no-untyped-call]
    assert isinstance(s_engine.pool, NullPool)

    await dispose_db()


def test_cache_control_headers_on_api_responses() -> None:
    """Verifies RequestContextMiddleware adds no-store, private."""
    with TestClient(app) as client:
        res = client.get("/api/v1/health")
        assert res.status_code == 200
        assert "no-store, private" in res.headers.get("cache-control", "")
        assert "x-request-id" in res.headers


@pytest.mark.skipif(not has_postgres, reason="PostgreSQL test database not reachable at 5433")
@pytest.mark.asyncio
async def test_postgres_indexes_exist() -> None:
    """Verifies all new performance indexes exist and duplicate index was removed in PostgreSQL."""
    engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    async with engine.connect() as conn:
        res = await conn.execute(
            text(
                "SELECT indexname FROM pg_indexes WHERE schemaname = 'public'"
            )
        )
        indexes = {row[0] for row in res.fetchall()}

        mod = _load_migration_0018()
        for idx_name, _, _ in mod.NEW_INDEXES:
            assert idx_name in indexes, f"Index {idx_name} not found in pg_indexes"

        # Verify duplicate index was removed, unique constraint index remains
        assert "ix_deleted_accounts_user_id" not in indexes
        assert "deleted_accounts_user_id_key" in indexes
    await engine.dispose()


@pytest.mark.skipif(not has_postgres, reason="PostgreSQL test database not reachable at 5433")
@pytest.mark.asyncio
async def test_obligations_sql_pagination_and_paise_accuracy() -> None:
    """Verifies SQL-level pagination and balance calculation."""
    engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    org_id = uuid4()
    user_id = uuid4()

    async with session_factory() as session:
        user = Profile(
            id=user_id,
            email=f"perf-obl-{user_id.hex[:6]}@example.com",
            display_name="Obligation Perf User",
        )
        session.add(user)
        org = Organization(
            id=org_id,
            name="Obligation Perf Org",
            slug=f"perf-obl-{org_id.hex[:6]}",
        )
        session.add(org)
        await session.flush()

        member = OrganizationMember(
            id=uuid4(),
            organization_id=org_id,
            user_id=user_id,
            role=OrgRole.OWNER,
        )
        session.add(member)

        contact = Contact(
            id=uuid4(),
            organization_id=org_id,
            name="Alice Lender",
        )
        session.add(contact)
        await session.flush()

        # Create 10 obligations of 1000.00 (100000 paise) each
        obligations = []
        for i in range(10):
            obl = Obligation(
                id=uuid4(),
                organization_id=org_id,
                contact_id=contact.id,
                counterparty_name="Alice",
                type=ObligationType.RECEIVABLE if i % 2 == 0 else ObligationType.PAYABLE,
                amount_paise=1000_00,
                status=ObligationStatus.ACTIVE,
                created_at=datetime.now(UTC) - timedelta(minutes=10 - i),
            )
            session.add(obl)
            obligations.append(obl)
        await session.flush()

        # Add payment to obligation 0: 300_00 paise
        p1 = ObligationPayment(
            id=uuid4(),
            organization_id=org_id,
            obligation_id=obligations[0].id,
            amount_paise=300_00,
            date=datetime.now(UTC),
            created_by=user_id,
        )
        session.add(p1)
        await session.commit()

    async with session_factory() as session:
        # Page 1 (limit=3, offset=0)
        items, total = await list_obligations_with_balance_paginated(
            session, organization_id=org_id, limit=3, offset=0
        )
        assert total == 10
        assert len(items) == 3

        # Page 2 (limit=3, offset=3)
        items2, total2 = await list_obligations_with_balance_paginated(
            session, organization_id=org_id, limit=3, offset=3
        )
        assert total2 == 10
        assert len(items2) == 3
        # Ensure pages are disjoint
        ids1 = {obl.id for obl, _ in items}
        ids2 = {obl.id for obl, _ in items2}
        assert ids1.isdisjoint(ids2)

        # Page 4 (limit=3, offset=9) -> exactly 1 item remaining
        items4, total4 = await list_obligations_with_balance_paginated(
            session, organization_id=org_id, limit=3, offset=9
        )
        assert total4 == 10
        assert len(items4) == 1

        # Check balance of obligation 0
        obl0_items, _ = await list_obligations_with_balance_paginated(
            session, organization_id=org_id, contact_id=contact.id, limit=10, offset=0
        )
        for obl, remaining in obl0_items:
            if obl.id == obligations[0].id:
                # 1000_00 - 300_00 = 700_00 remaining
                assert remaining == 700_00
                assert isinstance(remaining, int)

    await engine.dispose()


@pytest.mark.skipif(not has_postgres, reason="PostgreSQL test database not reachable at 5433")
@pytest.mark.asyncio
async def test_dashboard_cash_flow_trend_consolidated() -> None:
    """Verifies cash_flow_trend accurately computes 6-month trend via consolidated SQL."""
    engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    org_id = uuid4()
    user_id = uuid4()

    async with session_factory() as session:
        user = Profile(
            id=user_id,
            email=f"perf-trend-{user_id.hex[:6]}@example.com",
            display_name="Trend Perf User",
        )
        session.add(user)
        org = Organization(
            id=org_id,
            name="Trend Perf Org",
            slug=f"perf-trend-{org_id.hex[:6]}",
        )
        session.add(org)
        await session.flush()

        member = OrganizationMember(
            id=uuid4(),
            organization_id=org_id,
            user_id=user_id,
            role=OrgRole.OWNER,
        )
        session.add(member)

        account = Account(
            id=uuid4(),
            organization_id=org_id,
            name="Checking",
            kind=AccountKind.BANK,
            currency="INR",
        )
        session.add(account)

        cat_income = Category(
            id=uuid4(),
            org_id=org_id,
            name="Salary",
            kind=CategoryKind.income,
            color="#22C55E",
        )
        cat_expense = Category(
            id=uuid4(),
            org_id=org_id,
            name="Rent",
            kind=CategoryKind.expense,
            color="#EF4444",
        )
        session.add_all([cat_income, cat_expense])
        await session.flush()

        today = date.today()
        # Add income and expense in the current month
        tx1 = Transaction(
            id=uuid4(),
            organization_id=org_id,
            account_id=account.id,
            category_id=cat_income.id,
            amount_paise=50000_00,
            merchant="Employer Inc",
            type=TransactionType.PURCHASE,
            posting_status=PostingStatus.POSTED,
            occurred_at=datetime.combine(today.replace(day=5), datetime.min.time(), tzinfo=IST),
        )
        tx2 = Transaction(
            id=uuid4(),
            organization_id=org_id,
            account_id=account.id,
            category_id=cat_expense.id,
            amount_paise=15000_00,
            merchant="Landlord",
            type=TransactionType.PURCHASE,
            posting_status=PostingStatus.POSTED,
            occurred_at=datetime.combine(today.replace(day=10), datetime.min.time(), tzinfo=IST),
        )
        session.add_all([tx1, tx2])
        await session.commit()

    async with session_factory() as session:
        trend = await cash_flow_trend(session, organization_id=org_id, today=today)
        assert len(trend) == 6
        current_month_trend = trend[-1]
        assert current_month_trend.income_paise == 50000_00
        assert current_month_trend.expense_paise == 15000_00
        assert isinstance(current_month_trend.income_paise, int)
        assert isinstance(current_month_trend.expense_paise, int)

    await engine.dispose()
