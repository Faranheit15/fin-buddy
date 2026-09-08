"""Safe financial mutations: idempotency records and mutation concurrency guards.

- Create idempotency_records table for durable operation identity (RFC 9440)
- Add unique partial index on transactions(reverses_id) to prevent duplicate reversals
- Add unique constraint on emi_installments(plan_id, sequence_number)
- Add unique partial index on statement_line_candidates(committed_transaction_id) to prevent duplicate commits
- Add composite unique constraint on settlements(id, organization_id)
- Enable defense-in-depth RLS on idempotency_records

Revision ID: 20260908_0017
Revises: 20260907_0016
Create Date: 2026-09-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260908_0017"
down_revision: str | None = "20260907_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _auth_uid_exists() -> bool:
    """Check if Supabase auth.uid() function is present in this PostgreSQL instance."""
    bind = op.get_bind()
    try:
        return bool(
            bind.execute(
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


def upgrade() -> None:
    # 1. Idempotency records table
    op.create_table(
        "idempotency_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_path", sa.String(length=255), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("response_code", sa.Integer(), nullable=True),
        sa.Column("response_body", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_unique_constraint(
        "uq_idempotency_org_key",
        "idempotency_records",
        ["organization_id", "idempotency_key"],
    )
    op.create_index(
        "ix_idempotency_records_organization_id",
        "idempotency_records",
        ["organization_id"],
    )
    op.create_index(
        "ix_idempotency_records_user_id",
        "idempotency_records",
        ["user_id"],
    )
    op.create_index(
        "ix_idempotency_records_expires_at",
        "idempotency_records",
        ["expires_at"],
    )

    # 2. Prevent duplicate reversals for the same original transaction
    op.create_index(
        "uq_transactions_reverses_id",
        "transactions",
        ["reverses_id"],
        unique=True,
        postgresql_where=sa.text("reverses_id IS NOT NULL"),
    )

    # 3. Prevent duplicate installment sequences in the same EMI plan
    op.create_unique_constraint(
        "uq_emi_installments_plan_seq",
        "emi_installments",
        ["plan_id", "sequence_number"],
    )

    # 4. Prevent duplicate candidate line commits
    op.create_index(
        "uq_statement_lines_committed_tx",
        "statement_line_candidates",
        ["committed_transaction_id"],
        unique=True,
        postgresql_where=sa.text("committed_transaction_id IS NOT NULL"),
    )

    # 5. Composite tenant unique constraint on settlements
    op.create_unique_constraint(
        "uq_settlements_id_org",
        "settlements",
        ["id", "organization_id"],
    )

    # 6. Enable RLS on idempotency_records
    op.execute(sa.text("ALTER TABLE idempotency_records ENABLE ROW LEVEL SECURITY;"))
    if _auth_uid_exists():
        op.execute(
            sa.text(
                """
                CREATE POLICY idempotency_records_select_member ON idempotency_records
                    FOR SELECT USING (
                        organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    );
                CREATE POLICY idempotency_records_insert_member ON idempotency_records
                    FOR INSERT WITH CHECK (
                        organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    );
                CREATE POLICY idempotency_records_update_member ON idempotency_records
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
                CREATE POLICY idempotency_records_delete_member ON idempotency_records
                    FOR DELETE USING (
                        organization_id IN (
                            SELECT organization_id FROM organization_members
                            WHERE user_id = (SELECT auth.uid())
                        )
                    );
                """
            )
        )


def downgrade() -> None:
    if _auth_uid_exists():
        op.execute(sa.text("DROP POLICY IF EXISTS idempotency_records_delete_member ON idempotency_records"))
        op.execute(sa.text("DROP POLICY IF EXISTS idempotency_records_update_member ON idempotency_records"))
        op.execute(sa.text("DROP POLICY IF EXISTS idempotency_records_insert_member ON idempotency_records"))
        op.execute(sa.text("DROP POLICY IF EXISTS idempotency_records_select_member ON idempotency_records"))

    op.drop_constraint("uq_settlements_id_org", "settlements", type_="unique")
    op.drop_index("uq_statement_lines_committed_tx", table_name="statement_line_candidates")
    op.drop_constraint("uq_emi_installments_plan_seq", "emi_installments", type_="unique")
    op.drop_index("uq_transactions_reverses_id", table_name="transactions")
    op.drop_index("ix_idempotency_records_expires_at", table_name="idempotency_records")
    op.drop_index("ix_idempotency_records_user_id", table_name="idempotency_records")
    op.drop_index("ix_idempotency_records_organization_id", table_name="idempotency_records")
    op.drop_constraint("uq_idempotency_org_key", "idempotency_records", type_="unique")
    op.drop_table("idempotency_records")
