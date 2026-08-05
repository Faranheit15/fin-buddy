"""add_obligations_tables

Revision ID: c60597c9f79b
Revises: d01947b0fa9e
Create Date: 2026-08-05 23:45:07.858086

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c60597c9f79b"
down_revision: str | Sequence[str] | None = "d01947b0fa9e"
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
    _ensure_enum("obligation_type", "receivable', 'payable")
    _ensure_enum("obligation_status", "active', 'paid', 'defaulted")

    op.execute(sa.text("ALTER TYPE activity_action ADD VALUE IF NOT EXISTS 'obligation_create'"))
    op.execute(sa.text("ALTER TYPE activity_action ADD VALUE IF NOT EXISTS 'obligation_update'"))
    op.execute(sa.text("ALTER TYPE activity_action ADD VALUE IF NOT EXISTS 'obligation_payment'"))

    obligation_type = postgresql.ENUM(
        "receivable", "payable", name="obligation_type", create_type=False
    )
    obligation_status = postgresql.ENUM(
        "active", "paid", "defaulted", name="obligation_status", create_type=False
    )

    op.create_table(
        "obligations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("counterparty_name", sa.String(length=255), nullable=True),
        sa.Column("type", obligation_type, nullable=False),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("status", obligation_status, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_obligations_contact_id", "obligations", ["contact_id"], unique=False)
    op.create_index(
        "ix_obligations_organization_id", "obligations", ["organization_id"], unique=False
    )

    op.create_table(
        "obligation_payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("obligation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["obligation_id"], ["obligations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_obligation_payments_account_id", "obligation_payments", ["account_id"], unique=False
    )
    op.create_index("ix_obligation_payments_date", "obligation_payments", ["date"], unique=False)
    op.create_index(
        "ix_obligation_payments_obligation_id",
        "obligation_payments",
        ["obligation_id"],
        unique=False,
    )
    op.create_index(
        "ix_obligation_payments_organization_id",
        "obligation_payments",
        ["organization_id"],
        unique=False,
    )

    # RLS Policies
    op.execute(sa.text("ALTER TABLE obligations ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE obligation_payments ENABLE ROW LEVEL SECURITY"))

    if _auth_uid_exists():
        for table in ("obligations", "obligation_payments"):
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


def downgrade() -> None:
    if _auth_uid_exists():
        for table in ("obligation_payments", "obligations"):
            op.execute(sa.text(f"DROP POLICY IF EXISTS {table}_update_member ON {table}"))
            op.execute(sa.text(f"DROP POLICY IF EXISTS {table}_insert_member ON {table}"))
            op.execute(sa.text(f"DROP POLICY IF EXISTS {table}_select_member ON {table}"))

    op.execute(sa.text("ALTER TABLE obligation_payments DISABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE obligations DISABLE ROW LEVEL SECURITY"))

    op.drop_index("ix_obligation_payments_organization_id", table_name="obligation_payments")
    op.drop_index("ix_obligation_payments_obligation_id", table_name="obligation_payments")
    op.drop_index("ix_obligation_payments_date", table_name="obligation_payments")
    op.drop_index("ix_obligation_payments_account_id", table_name="obligation_payments")
    op.drop_table("obligation_payments")

    op.drop_index("ix_obligations_organization_id", table_name="obligations")
    op.drop_index("ix_obligations_contact_id", table_name="obligations")
    op.drop_table("obligations")

    op.execute(sa.text("DROP TYPE IF EXISTS obligation_status"))
    op.execute(sa.text("DROP TYPE IF EXISTS obligation_type"))
