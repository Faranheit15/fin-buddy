"""Supabase security boundary: RLS, grants, and routine execution hardening.

Revision ID: 20260907_0015
Revises: 20260810_0014
Create Date: 2026-09-07
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260907_0015"
down_revision: str | None = "20260810_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# All 23 application tables in the public schema
ALL_APPLICATION_TABLES = [
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
]

# Tables with newly enabled RLS in this migration (accounts, obligations, obligation_payments,
# emi_plans, emi_installments, record_shares previously had RLS enabled in earlier migrations)
NEWLY_ENABLED_RLS_TABLES = [
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
    "categories",
    "rate_limit_windows",
]

# Standard organization-scoped tables with organization_id column
STANDARD_ORG_TABLES = [
    "contacts",
    "credit_cards",
    "statements",
    "statement_line_candidates",
    "transactions",
    "settlements",
    "accounts",
    "obligations",
    "obligation_payments",
    "emi_plans",
]


def _auth_uid_exists() -> bool:
    """Check if Supabase auth.uid() function is present in database."""
    try:
        conn = op.get_bind()
        return bool(
            conn.execute(
                sa.text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_proc p
                        JOIN pg_namespace n ON p.pronamespace = n.oid
                        WHERE n.nspname = 'auth' AND p.proname = 'uid'
                    )
                    """
                )
            ).scalar()
        )
    except Exception:
        return False


def _drop_existing_partial_policies() -> None:
    """Drop older partial policies that lacked WITH CHECK or InitPlan optimization."""
    # accounts
    op.execute(sa.text("DROP POLICY IF EXISTS accounts_select_member ON accounts"))
    op.execute(sa.text("DROP POLICY IF EXISTS accounts_insert_member ON accounts"))
    op.execute(sa.text("DROP POLICY IF EXISTS accounts_update_member ON accounts"))

    # obligations & obligation_payments
    op.execute(sa.text("DROP POLICY IF EXISTS obligations_select_member ON obligations"))
    op.execute(sa.text("DROP POLICY IF EXISTS obligations_insert_member ON obligations"))
    op.execute(sa.text("DROP POLICY IF EXISTS obligations_update_member ON obligations"))
    op.execute(
        sa.text("DROP POLICY IF EXISTS obligation_payments_select_member ON obligation_payments")
    )
    op.execute(
        sa.text("DROP POLICY IF EXISTS obligation_payments_insert_member ON obligation_payments")
    )
    op.execute(
        sa.text("DROP POLICY IF EXISTS obligation_payments_update_member ON obligation_payments")
    )

    # emi_plans & emi_installments
    op.execute(sa.text("DROP POLICY IF EXISTS emi_plans_select_member ON emi_plans"))
    op.execute(sa.text("DROP POLICY IF EXISTS emi_plans_insert_member ON emi_plans"))
    op.execute(sa.text("DROP POLICY IF EXISTS emi_plans_update_member ON emi_plans"))
    op.execute(sa.text("DROP POLICY IF EXISTS emi_installments_select_member ON emi_installments"))
    op.execute(sa.text("DROP POLICY IF EXISTS emi_installments_insert_member ON emi_installments"))
    op.execute(sa.text("DROP POLICY IF EXISTS emi_installments_update_member ON emi_installments"))

    # record_shares
    op.execute(sa.text("DROP POLICY IF EXISTS record_shares_select ON record_shares"))


def _create_hardened_policies() -> None:
    """Create comprehensive defense-in-depth policies with WITH CHECK and InitPlan subqueries."""
    # 1. profiles: user owns their own profile
    op.execute(
        sa.text(
            """
            CREATE POLICY profiles_select_own ON profiles
                FOR SELECT USING (id = (SELECT auth.uid()));
            CREATE POLICY profiles_update_own ON profiles
                FOR UPDATE USING (id = (SELECT auth.uid()))
                WITH CHECK (id = (SELECT auth.uid()));
            """
        )
    )

    # 2. organizations: members can view and update their organizations
    op.execute(
        sa.text(
            """
            CREATE POLICY organizations_select_member ON organizations
                FOR SELECT USING (
                    id IN (
                        SELECT organization_id FROM organization_members
                        WHERE user_id = (SELECT auth.uid())
                    )
                );
            CREATE POLICY organizations_update_member ON organizations
                FOR UPDATE USING (
                    id IN (
                        SELECT organization_id FROM organization_members
                        WHERE user_id = (SELECT auth.uid())
                    )
                )
                WITH CHECK (
                    id IN (
                        SELECT organization_id FROM organization_members
                        WHERE user_id = (SELECT auth.uid())
                    )
                );
            """
        )
    )

    # 3. organization_members: users can view their own memberships (prevents recursive RLS evaluation)
    op.execute(
        sa.text(
            """
            CREATE POLICY organization_members_select_own ON organization_members
                FOR SELECT USING (user_id = (SELECT auth.uid()));
            """
        )
    )

    # 4. Standard organization-scoped tables (organization_id column)
    for table in STANDARD_ORG_TABLES:
        op.execute(
            sa.text(
                f"""
                CREATE POLICY {table}_select_member ON {table}
                    FOR SELECT USING (
                        organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    );
                CREATE POLICY {table}_insert_member ON {table}
                    FOR INSERT WITH CHECK (
                        organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    );
                CREATE POLICY {table}_update_member ON {table}
                    FOR UPDATE USING (
                        organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    )
                    WITH CHECK (
                        organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    );
                CREATE POLICY {table}_delete_member ON {table}
                    FOR DELETE USING (
                        organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    );
                """
            )
        )

    # 5. categories: uses org_id column
    op.execute(
        sa.text(
            """
            CREATE POLICY categories_select_member ON categories
                FOR SELECT USING (
                    org_id IN (
                        SELECT organization_id FROM organization_members
                        WHERE user_id = (SELECT auth.uid())
                    )
                );
            CREATE POLICY categories_insert_member ON categories
                FOR INSERT WITH CHECK (
                    org_id IN (
                        SELECT organization_id FROM organization_members
                        WHERE user_id = (SELECT auth.uid())
                    )
                );
            CREATE POLICY categories_update_member ON categories
                FOR UPDATE USING (
                    org_id IN (
                        SELECT organization_id FROM organization_members
                        WHERE user_id = (SELECT auth.uid())
                    )
                )
                WITH CHECK (
                    org_id IN (
                        SELECT organization_id FROM organization_members
                        WHERE user_id = (SELECT auth.uid())
                    )
                );
            CREATE POLICY categories_delete_member ON categories
                FOR DELETE USING (
                    org_id IN (
                        SELECT organization_id FROM organization_members
                        WHERE user_id = (SELECT auth.uid())
                    )
                );
            """
        )
    )

    # 6. transaction_splits: joins via transactions
    op.execute(
        sa.text(
            """
            CREATE POLICY transaction_splits_select_member ON transaction_splits
                FOR SELECT USING (
                    transaction_id IN (
                        SELECT id FROM transactions
                        WHERE organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    )
                );
            CREATE POLICY transaction_splits_insert_member ON transaction_splits
                FOR INSERT WITH CHECK (
                    transaction_id IN (
                        SELECT id FROM transactions
                        WHERE organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    )
                );
            CREATE POLICY transaction_splits_update_member ON transaction_splits
                FOR UPDATE USING (
                    transaction_id IN (
                        SELECT id FROM transactions
                        WHERE organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    )
                )
                WITH CHECK (
                    transaction_id IN (
                        SELECT id FROM transactions
                        WHERE organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    )
                );
            CREATE POLICY transaction_splits_delete_member ON transaction_splits
                FOR DELETE USING (
                    transaction_id IN (
                        SELECT id FROM transactions
                        WHERE organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    )
                );
            """
        )
    )

    # 7. emi_installments: joins via emi_plans
    op.execute(
        sa.text(
            """
            CREATE POLICY emi_installments_select_member ON emi_installments
                FOR SELECT USING (
                    plan_id IN (
                        SELECT id FROM emi_plans
                        WHERE organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    )
                );
            CREATE POLICY emi_installments_insert_member ON emi_installments
                FOR INSERT WITH CHECK (
                    plan_id IN (
                        SELECT id FROM emi_plans
                        WHERE organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    )
                );
            CREATE POLICY emi_installments_update_member ON emi_installments
                FOR UPDATE USING (
                    plan_id IN (
                        SELECT id FROM emi_plans
                        WHERE organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    )
                )
                WITH CHECK (
                    plan_id IN (
                        SELECT id FROM emi_plans
                        WHERE organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    )
                );
            CREATE POLICY emi_installments_delete_member ON emi_installments
                FOR DELETE USING (
                    plan_id IN (
                        SELECT id FROM emi_plans
                        WHERE organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    )
                );
            """
        )
    )

    # 8. record_shares: recipient or org member
    op.execute(
        sa.text(
            """
            CREATE POLICY record_shares_select_member ON record_shares
                FOR SELECT USING (
                    shared_with_user_id = (SELECT auth.uid()) OR
                    organization_id IN (
                        SELECT organization_id FROM organization_members
                        WHERE user_id = (SELECT auth.uid())
                    )
                );
            CREATE POLICY record_shares_insert_member ON record_shares
                FOR INSERT WITH CHECK (
                    organization_id IN (
                        SELECT organization_id FROM organization_members
                        WHERE user_id = (SELECT auth.uid())
                    )
                );
            CREATE POLICY record_shares_update_member ON record_shares
                FOR UPDATE USING (
                    organization_id IN (
                        SELECT organization_id FROM organization_members
                        WHERE user_id = (SELECT auth.uid())
                    )
                )
                WITH CHECK (
                    organization_id IN (
                        SELECT organization_id FROM organization_members
                        WHERE user_id = (SELECT auth.uid())
                    )
                );
            CREATE POLICY record_shares_delete_member ON record_shares
                FOR DELETE USING (
                    organization_id IN (
                        SELECT organization_id FROM organization_members
                        WHERE user_id = (SELECT auth.uid())
                    )
                );
            """
        )
    )

    # 9. in_app_notifications: user owns notifications
    op.execute(
        sa.text(
            """
            CREATE POLICY in_app_notifications_select_own ON in_app_notifications
                FOR SELECT USING (user_id = (SELECT auth.uid()));
            CREATE POLICY in_app_notifications_update_own ON in_app_notifications
                FOR UPDATE USING (user_id = (SELECT auth.uid()))
                WITH CHECK (user_id = (SELECT auth.uid()));
            CREATE POLICY in_app_notifications_delete_own ON in_app_notifications
                FOR DELETE USING (user_id = (SELECT auth.uid()));
            """
        )
    )


def upgrade() -> None:
    # 1. Enable RLS on all remaining application tables (ENABLE without FORCE so table owner / service-role operates)
    for table in NEWLY_ENABLED_RLS_TABLES:
        op.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))

    # 2. Revoke public Data API / PostgREST grants from anon and authenticated roles
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                -- Revoke privileges on all current tables, sequences, and routines in public schema
                REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;
                REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
                REVOKE ALL ON ALL ROUTINES IN SCHEMA public FROM anon, authenticated, PUBLIC;

                -- Revoke default privileges for future objects created in public schema
                ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon, authenticated;
                ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated;
                ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON ROUTINES FROM anon, authenticated, PUBLIC;
            EXCEPTION WHEN OTHERS THEN
                -- Safe fallback for plain PostgreSQL environments lacking Supabase anon/authenticated roles
                NULL;
            END $$;
            """
        )
    )

    # 3. Create hardened policies in Supabase environments where auth.uid() exists
    if _auth_uid_exists():
        _drop_existing_partial_policies()
        _create_hardened_policies()


def downgrade() -> None:
    # 1. Drop hardened policies if auth.uid() exists
    if _auth_uid_exists():
        op.execute(sa.text("DROP POLICY IF EXISTS profiles_select_own ON profiles"))
        op.execute(sa.text("DROP POLICY IF EXISTS profiles_update_own ON profiles"))
        op.execute(sa.text("DROP POLICY IF EXISTS organizations_select_member ON organizations"))
        op.execute(sa.text("DROP POLICY IF EXISTS organizations_update_member ON organizations"))
        op.execute(
            sa.text("DROP POLICY IF EXISTS organization_members_select_own ON organization_members")
        )

        for table in STANDARD_ORG_TABLES:
            op.execute(sa.text(f"DROP POLICY IF EXISTS {table}_select_member ON {table}"))
            op.execute(sa.text(f"DROP POLICY IF EXISTS {table}_insert_member ON {table}"))
            op.execute(sa.text(f"DROP POLICY IF EXISTS {table}_update_member ON {table}"))
            op.execute(sa.text(f"DROP POLICY IF EXISTS {table}_delete_member ON {table}"))

        op.execute(sa.text("DROP POLICY IF EXISTS categories_select_member ON categories"))
        op.execute(sa.text("DROP POLICY IF EXISTS categories_insert_member ON categories"))
        op.execute(sa.text("DROP POLICY IF EXISTS categories_update_member ON categories"))
        op.execute(sa.text("DROP POLICY IF EXISTS categories_delete_member ON categories"))

        op.execute(
            sa.text("DROP POLICY IF EXISTS transaction_splits_select_member ON transaction_splits")
        )
        op.execute(
            sa.text("DROP POLICY IF EXISTS transaction_splits_insert_member ON transaction_splits")
        )
        op.execute(
            sa.text("DROP POLICY IF EXISTS transaction_splits_update_member ON transaction_splits")
        )
        op.execute(
            sa.text("DROP POLICY IF EXISTS transaction_splits_delete_member ON transaction_splits")
        )

        op.execute(
            sa.text("DROP POLICY IF EXISTS emi_installments_select_member ON emi_installments")
        )
        op.execute(
            sa.text("DROP POLICY IF EXISTS emi_installments_insert_member ON emi_installments")
        )
        op.execute(
            sa.text("DROP POLICY IF EXISTS emi_installments_update_member ON emi_installments")
        )
        op.execute(
            sa.text("DROP POLICY IF EXISTS emi_installments_delete_member ON emi_installments")
        )

        op.execute(sa.text("DROP POLICY IF EXISTS record_shares_select_member ON record_shares"))
        op.execute(sa.text("DROP POLICY IF EXISTS record_shares_insert_member ON record_shares"))
        op.execute(sa.text("DROP POLICY IF EXISTS record_shares_update_member ON record_shares"))
        op.execute(sa.text("DROP POLICY IF EXISTS record_shares_delete_member ON record_shares"))

        op.execute(
            sa.text(
                "DROP POLICY IF EXISTS in_app_notifications_select_own ON in_app_notifications"
            )
        )
        op.execute(
            sa.text(
                "DROP POLICY IF EXISTS in_app_notifications_update_own ON in_app_notifications"
            )
        )
        op.execute(
            sa.text(
                "DROP POLICY IF EXISTS in_app_notifications_delete_own ON in_app_notifications"
            )
        )

        # Restore original partial policies on accounts
        op.execute(
            sa.text(
                """
                CREATE POLICY accounts_select_member ON accounts
                  FOR SELECT USING (
                    organization_id IN (
                      SELECT organization_id FROM organization_members
                      WHERE user_id = auth.uid()
                    )
                  );
                CREATE POLICY accounts_insert_member ON accounts
                  FOR INSERT WITH CHECK (
                    organization_id IN (
                      SELECT organization_id FROM organization_members
                      WHERE user_id = auth.uid()
                    )
                  );
                CREATE POLICY accounts_update_member ON accounts
                  FOR UPDATE USING (
                    organization_id IN (
                      SELECT organization_id FROM organization_members
                      WHERE user_id = auth.uid()
                    )
                  );
                """
            )
        )

    # 2. Disable RLS on the newly enabled tables
    for table in NEWLY_ENABLED_RLS_TABLES:
        op.execute(sa.text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY"))
