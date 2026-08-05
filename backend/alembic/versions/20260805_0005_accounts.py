"""Create accounts table, backfill from credit_cards, enable RLS policies.

Revision ID: 20260805_0005
Revises: 20260805_0004
Create Date: 2026-08-05
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260805_0005"
down_revision: str | None = "20260805_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

account_kind = postgresql.ENUM(
    "bank",
    "cash",
    "wallet",
    "credit_card",
    name="account_kind",
    create_type=False,
)


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


def _backfill_card_accounts() -> None:
    """Insert one credit_card account per card (Python uuid4 — no gen_random_uuid)."""
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            """
            SELECT c.id, c.organization_id, c.nickname, c.issuer, c.currency
            FROM credit_cards c
            WHERE NOT EXISTS (
                SELECT 1 FROM accounts a WHERE a.credit_card_id = c.id
            )
            """
        )
    ).fetchall()
    for card_id, organization_id, nickname, issuer, currency in rows:
        conn.execute(
            sa.text(
                """
                INSERT INTO accounts (
                    id, organization_id, kind, name, institution, currency,
                    credit_card_id, archived_at, created_at, updated_at
                ) VALUES (
                    :id, :organization_id, 'credit_card', :name, :institution, :currency,
                    :credit_card_id, NULL, now(), now()
                )
                """
            ),
            {
                "id": str(uuid4()),
                "organization_id": str(organization_id),
                "name": nickname,
                "institution": issuer,
                "currency": currency,
                "credit_card_id": str(card_id),
            },
        )


def upgrade() -> None:
    _ensure_enum("account_kind", "bank', 'cash', 'wallet', 'credit_card")

    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", account_kind, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("institution", sa.String(length=120), nullable=True),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default="INR",
        ),
        sa.Column("credit_card_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["credit_card_id"],
            ["credit_cards.id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "(kind = 'credit_card' AND credit_card_id IS NOT NULL) OR "
            "(kind <> 'credit_card' AND credit_card_id IS NULL)",
            name="ck_accounts_kind_card",
        ),
    )

    op.create_index("ix_accounts_organization_id", "accounts", ["organization_id"])
    op.create_index("ix_accounts_org_kind", "accounts", ["organization_id", "kind"])
    op.create_index(
        "ix_accounts_org_active",
        "accounts",
        ["organization_id"],
        postgresql_where=sa.text("archived_at IS NULL"),
    )
    op.create_index(
        "uq_accounts_credit_card_id",
        "accounts",
        ["credit_card_id"],
        unique=True,
        postgresql_where=sa.text("credit_card_id IS NOT NULL"),
    )

    _backfill_card_accounts()

    # Defense-in-depth RLS. Skip FORCE so table owner / service_role can still operate.
    # Policies require Supabase auth.uid(); skip when unavailable (plain Postgres CI).
    op.execute(sa.text("ALTER TABLE accounts ENABLE ROW LEVEL SECURITY"))
    if _auth_uid_exists():
        op.execute(
            sa.text(
                """
                CREATE POLICY accounts_select_member ON accounts
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
                """
                CREATE POLICY accounts_insert_member ON accounts
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
                """
                CREATE POLICY accounts_update_member ON accounts
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
        op.execute(sa.text("DROP POLICY IF EXISTS accounts_update_member ON accounts"))
        op.execute(sa.text("DROP POLICY IF EXISTS accounts_insert_member ON accounts"))
        op.execute(sa.text("DROP POLICY IF EXISTS accounts_select_member ON accounts"))
    op.execute(sa.text("ALTER TABLE accounts DISABLE ROW LEVEL SECURITY"))

    op.drop_index("uq_accounts_credit_card_id", table_name="accounts")
    op.drop_index("ix_accounts_org_active", table_name="accounts")
    op.drop_index("ix_accounts_org_kind", table_name="accounts")
    op.drop_index("ix_accounts_organization_id", table_name="accounts")
    op.drop_table("accounts")
    op.execute(sa.text("DROP TYPE IF EXISTS account_kind"))
