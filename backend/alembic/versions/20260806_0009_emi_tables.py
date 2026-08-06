"""emi_tables

Revision ID: 20260806_0009
Revises: c60597c9f79b
Create Date: 2026-08-06 12:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260806_0009"
down_revision: str | Sequence[str] | None = "c60597c9f79b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _ensure_enum(name: str, values_sql: str) -> None:
    op.execute(
        sa.text(
            f"""
            DO $$ BEGIN
                CREATE TYPE {name} AS ENUM ('{values_sql}');
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END $$;
            """
        )
    )


def _auth_uid_exists() -> bool:
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


def upgrade() -> None:
    _ensure_enum("emi_plan_status", "active', 'completed")
    _ensure_enum("emi_installment_status", "pending', 'paid', 'overdue")

    op.execute(sa.text("ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'emi_interest'"))
    op.execute(sa.text("ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'emi_gst'"))
    op.execute(sa.text("ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'emi_fee'"))

    emi_plan_status = postgresql.ENUM(
        "active", "completed", name="emi_plan_status", create_type=False
    )
    emi_installment_status = postgresql.ENUM(
        "pending", "paid", "overdue", name="emi_installment_status", create_type=False
    )

    op.create_table(
        "emi_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("credit_card_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reference_transaction_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("principal_paise", sa.BigInteger(), nullable=False),
        sa.Column("interest_rate_bps", sa.Integer(), nullable=False),
        sa.Column("tenure_months", sa.Integer(), nullable=False),
        sa.Column("status", emi_plan_status, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["credit_card_id"], ["credit_cards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reference_transaction_id"], ["transactions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_emi_plans_credit_card_id", "emi_plans", ["credit_card_id"], unique=False)
    op.create_index(
        "ix_emi_plans_organization_id", "emi_plans", ["organization_id"], unique=False
    )

    op.create_table(
        "emi_installments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("principal_paise", sa.BigInteger(), nullable=False),
        sa.Column("interest_paise", sa.BigInteger(), nullable=False),
        sa.Column("fees_paise", sa.BigInteger(), nullable=False),
        sa.Column("gst_paise", sa.BigInteger(), nullable=False),
        sa.Column("total_paise", sa.BigInteger(), nullable=False),
        sa.Column("status", emi_installment_status, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["emi_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_emi_installments_plan_id", "emi_installments", ["plan_id"], unique=False
    )

    # RLS Policies
    op.execute(sa.text("ALTER TABLE emi_plans ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE emi_installments ENABLE ROW LEVEL SECURITY"))

    if _auth_uid_exists():
        for table in ("emi_plans", "emi_installments"):
            # emi_installments doesn't have organization_id directly, so policy must join via emi_plans
            if table == "emi_plans":
                op.execute(
                    sa.text(
                        f"""
                        CREATE POLICY {table}_select_member ON {table}
                          FOR SELECT USING (
                            organization_id IN (
                              SELECT organization_id FROM organization_members
                              WHERE user_id = auth.uid()
                            )
                          )
                        """
                    )
                )
                op.execute(
                    sa.text(
                        f"""
                        CREATE POLICY {table}_insert_member ON {table}
                          FOR INSERT WITH CHECK (
                            organization_id IN (
                              SELECT organization_id FROM organization_members
                              WHERE user_id = auth.uid()
                            )
                          )
                        """
                    )
                )
                op.execute(
                    sa.text(
                        f"""
                        CREATE POLICY {table}_update_member ON {table}
                          FOR UPDATE USING (
                            organization_id IN (
                              SELECT organization_id FROM organization_members
                              WHERE user_id = auth.uid()
                            )
                          )
                        """
                    )
                )
            else:
                op.execute(
                    sa.text(
                        f"""
                        CREATE POLICY {table}_select_member ON {table}
                          FOR SELECT USING (
                            plan_id IN (
                              SELECT id FROM emi_plans
                              WHERE organization_id IN (
                                SELECT organization_id FROM organization_members
                                WHERE user_id = auth.uid()
                              )
                            )
                          )
                        """
                    )
                )
                op.execute(
                    sa.text(
                        f"""
                        CREATE POLICY {table}_insert_member ON {table}
                          FOR INSERT WITH CHECK (
                            plan_id IN (
                              SELECT id FROM emi_plans
                              WHERE organization_id IN (
                                SELECT organization_id FROM organization_members
                                WHERE user_id = auth.uid()
                              )
                            )
                          )
                        """
                    )
                )
                op.execute(
                    sa.text(
                        f"""
                        CREATE POLICY {table}_update_member ON {table}
                          FOR UPDATE USING (
                            plan_id IN (
                              SELECT id FROM emi_plans
                              WHERE organization_id IN (
                                SELECT organization_id FROM organization_members
                                WHERE user_id = auth.uid()
                              )
                            )
                          )
                        """
                    )
                )


def downgrade() -> None:
    if _auth_uid_exists():
        for table in ("emi_installments", "emi_plans"):
            op.execute(sa.text(f"DROP POLICY IF EXISTS {table}_update_member ON {table}"))
            op.execute(sa.text(f"DROP POLICY IF EXISTS {table}_insert_member ON {table}"))
            op.execute(sa.text(f"DROP POLICY IF EXISTS {table}_select_member ON {table}"))

    op.execute(sa.text("ALTER TABLE emi_installments DISABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE emi_plans DISABLE ROW LEVEL SECURITY"))

    op.drop_index("ix_emi_installments_plan_id", table_name="emi_installments")
    op.drop_table("emi_installments")

    op.drop_index("ix_emi_plans_organization_id", table_name="emi_plans")
    op.drop_index("ix_emi_plans_credit_card_id", table_name="emi_plans")
    op.drop_table("emi_plans")

    op.execute(sa.text("DROP TYPE IF EXISTS emi_installment_status"))
    op.execute(sa.text("DROP TYPE IF EXISTS emi_plan_status"))
