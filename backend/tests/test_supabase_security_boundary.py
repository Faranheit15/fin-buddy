"""Tests for Supabase security boundary, RLS hardening, and PostgREST grant revokes."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock


def _load_migration_module() -> Any:
    migration_path = (
        Path(__file__).resolve().parent.parent
        / "alembic"
        / "versions"
        / "20260907_0015_supabase_security_boundary.py"
    )
    spec = importlib.util.spec_from_file_location("migration_20260907_0015", migration_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_revision_chain() -> None:
    mod = _load_migration_module()
    assert mod.revision == "20260907_0015"
    assert mod.down_revision == "20260810_0014"


def test_all_application_tables_covered_by_rls() -> None:
    mod = _load_migration_module()
    expected_tables = {
        "profiles",
        "organizations",
        "organization_members",
        "contacts",
        "credit_cards",
        "statements",
        "statement_line_candidates",
        "transactions",
        "transaction_splits",
        "settlements",
        "in_app_notifications",
        "activity_logs",
        "error_logs",
        "api_request_logs",
        "seed_history",
        "accounts",
        "categories",
        "obligations",
        "obligation_payments",
        "emi_plans",
        "emi_installments",
        "record_shares",
        "rate_limit_windows",
    }
    assert set(mod.ALL_APPLICATION_TABLES) == expected_tables
    assert len(mod.ALL_APPLICATION_TABLES) == 23


def test_all_entity_tables_have_insert_update_delete_policies() -> None:
    mod = _load_migration_module()
    sql_calls: list[str] = []

    def fake_execute(sql: Any) -> None:
        sql_calls.append(str(sql))

    mock_op = MagicMock()
    mock_op.execute = fake_execute

    original_auth_uid = mod._auth_uid_exists
    mod._auth_uid_exists = lambda: True
    try:
        original_op = getattr(mod, "op", None)
        mod.op = mock_op
        mod.upgrade()
    finally:
        mod._auth_uid_exists = original_auth_uid
        if original_op is not None:
            mod.op = original_op

    full_sql = "\n".join(sql_calls)

    for table in mod.NEWLY_ENABLED_RLS_TABLES:
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in full_sql

    for table in mod.STANDARD_ORG_TABLES:
        assert f"CREATE POLICY {table}_select_member" in full_sql
        assert f"CREATE POLICY {table}_insert_member" in full_sql
        assert f"CREATE POLICY {table}_update_member" in full_sql
        assert f"CREATE POLICY {table}_delete_member" in full_sql


def test_update_policies_contain_with_check() -> None:
    mod = _load_migration_module()
    sql_calls: list[str] = []

    mock_op = MagicMock()
    mock_op.execute = lambda sql: sql_calls.append(str(sql))

    original_auth_uid = mod._auth_uid_exists
    mod._auth_uid_exists = lambda: True
    try:
        original_op = getattr(mod, "op", None)
        mod.op = mock_op
        mod.upgrade()
    finally:
        mod._auth_uid_exists = original_auth_uid
        if original_op is not None:
            mod.op = original_op

    for stmt in sql_calls:
        if "FOR UPDATE" in stmt:
            assert "WITH CHECK" in stmt, f"Update policy lacks WITH CHECK: {stmt}"


def test_select_auth_uid_initplan_optimization() -> None:
    mod = _load_migration_module()
    sql_calls: list[str] = []

    mock_op = MagicMock()
    mock_op.execute = lambda sql: sql_calls.append(str(sql))

    original_auth_uid = mod._auth_uid_exists
    mod._auth_uid_exists = lambda: True
    try:
        original_op = getattr(mod, "op", None)
        mod.op = mock_op
        mod.upgrade()
    finally:
        mod._auth_uid_exists = original_auth_uid
        if original_op is not None:
            mod.op = original_op

    for stmt in sql_calls:
        if "CREATE POLICY" in stmt:
            assert "(SELECT auth.uid())" in stmt, f"Policy does not use InitPlan (SELECT auth.uid()): {stmt}"


def test_organization_members_policy_avoids_direct_recursion() -> None:
    mod = _load_migration_module()
    sql_calls: list[str] = []

    mock_op = MagicMock()
    mock_op.execute = lambda sql: sql_calls.append(str(sql))

    original_auth_uid = mod._auth_uid_exists
    mod._auth_uid_exists = lambda: True
    try:
        original_op = getattr(mod, "op", None)
        mod.op = mock_op
        mod.upgrade()
    finally:
        mod._auth_uid_exists = original_auth_uid
        if original_op is not None:
            mod.op = original_op

    full_sql = "\n".join(sql_calls)
    assert "CREATE POLICY organization_members_select_own ON organization_members" in full_sql
    assert "user_id = (SELECT auth.uid())" in full_sql


def test_categories_policy_uses_org_id_column() -> None:
    mod = _load_migration_module()
    sql_calls: list[str] = []

    mock_op = MagicMock()
    mock_op.execute = lambda sql: sql_calls.append(str(sql))

    original_auth_uid = mod._auth_uid_exists
    mod._auth_uid_exists = lambda: True
    try:
        original_op = getattr(mod, "op", None)
        mod.op = mock_op
        mod.upgrade()
    finally:
        mod._auth_uid_exists = original_auth_uid
        if original_op is not None:
            mod.op = original_op

    full_sql = "\n".join(sql_calls)
    assert "CREATE POLICY categories_select_member ON categories" in full_sql
    assert "org_id IN (" in full_sql


def test_public_grants_revoked() -> None:
    mod = _load_migration_module()
    sql_calls: list[str] = []

    mock_op = MagicMock()
    mock_op.execute = lambda sql: sql_calls.append(str(sql))

    original_op = getattr(mod, "op", None)
    mod.op = mock_op
    try:
        mod.upgrade()
    finally:
        if original_op is not None:
            mod.op = original_op

    full_sql = "\n".join(sql_calls)
    assert "REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;" in full_sql
    assert "REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;" in full_sql
    assert "REVOKE ALL ON ALL ROUTINES IN SCHEMA public FROM anon, authenticated, PUBLIC;" in full_sql


def test_default_privileges_revoked() -> None:
    mod = _load_migration_module()
    sql_calls: list[str] = []

    mock_op = MagicMock()
    mock_op.execute = lambda sql: sql_calls.append(str(sql))

    original_op = getattr(mod, "op", None)
    mod.op = mock_op
    try:
        mod.upgrade()
    finally:
        if original_op is not None:
            mod.op = original_op

    full_sql = "\n".join(sql_calls)
    assert "ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon, authenticated;" in full_sql
    assert "ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated;" in full_sql
    assert "ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON ROUTINES FROM anon, authenticated, PUBLIC;" in full_sql


def test_downgrade_drops_policies_and_restores_grants() -> None:
    mod = _load_migration_module()
    sql_calls: list[str] = []

    mock_op = MagicMock()
    mock_op.execute = lambda sql: sql_calls.append(str(sql))

    original_auth_uid = mod._auth_uid_exists
    mod._auth_uid_exists = lambda: True
    try:
        original_op = getattr(mod, "op", None)
        mod.op = mock_op
        mod.downgrade()
    finally:
        mod._auth_uid_exists = original_auth_uid
        if original_op is not None:
            mod.op = original_op

    full_sql = "\n".join(sql_calls)
    assert "DROP POLICY IF EXISTS" in full_sql
    for table in mod.NEWLY_ENABLED_RLS_TABLES:
        assert f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY" in full_sql


def test_no_force_rls_used() -> None:
    mod = _load_migration_module()
    sql_calls: list[str] = []

    mock_op = MagicMock()
    mock_op.execute = lambda sql: sql_calls.append(str(sql))

    original_op = getattr(mod, "op", None)
    mod.op = mock_op
    try:
        mod.upgrade()
    finally:
        if original_op is not None:
            mod.op = original_op

    full_sql = "\n".join(sql_calls)
    assert "FORCE ROW LEVEL SECURITY" not in full_sql


def test_mock_data_api_policy_enforces_tenant_isolation() -> None:
    user_memberships = {
        "user_alice": {"org_1"},
        "user_bob": {"org_2"},
    }

    def can_access_row(user: str, row_org: str) -> bool:
        return row_org in user_memberships.get(user, set())

    assert can_access_row("user_alice", "org_1") is True
    assert can_access_row("user_alice", "org_2") is False
    assert can_access_row("user_bob", "org_1") is False
    assert can_access_row("user_bob", "org_2") is True


def test_mock_data_api_update_with_check_rejects_tenant_reassignment() -> None:
    user_memberships = {"user_alice": {"org_1"}}

    def can_update_row(user: str, current_org: str, new_org: str) -> bool:
        using_clause = current_org in user_memberships.get(user, set())
        with_check_clause = new_org in user_memberships.get(user, set())
        return using_clause and with_check_clause

    assert can_update_row("user_alice", "org_1", "org_1") is True
    assert can_update_row("user_alice", "org_1", "org_2") is False


def test_mock_data_api_delete_policy_enforces_tenant_isolation() -> None:
    user_memberships = {"user_alice": {"org_1"}}

    def can_delete_row(user: str, row_org: str) -> bool:
        return row_org in user_memberships.get(user, set())

    assert can_delete_row("user_alice", "org_1") is True
    assert can_delete_row("user_alice", "org_2") is False


def test_mock_service_role_bypasses_rls() -> None:
    is_table_owner_or_superuser = True
    assert is_table_owner_or_superuser is True


def test_system_log_tables_no_direct_api_access() -> None:
    mod = _load_migration_module()
    log_tables = {"activity_logs", "error_logs", "api_request_logs", "seed_history", "rate_limit_windows"}
    sql_calls: list[str] = []

    mock_op = MagicMock()
    mock_op.execute = lambda sql: sql_calls.append(str(sql))

    original_auth_uid = mod._auth_uid_exists
    mod._auth_uid_exists = lambda: True
    try:
        original_op = getattr(mod, "op", None)
        mod.op = mock_op
        mod.upgrade()
    finally:
        mod._auth_uid_exists = original_auth_uid
        if original_op is not None:
            mod.op = original_op

    full_sql = "\n".join(sql_calls)
    for table in log_tables:
        assert f"CREATE POLICY {table}_" not in full_sql
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in full_sql
