"""Auditable ledger: posting_status, reverse links, adjustment/reversal types.

Revision ID: 20260805_0003
Revises: 20260728_0002
Create Date: 2026-08-05
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260805_0003"
down_revision: str | None = "20260728_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

posting_status = postgresql.ENUM(
    "draft",
    "posted",
    name="posting_status",
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


def upgrade() -> None:
    _ensure_enum("posting_status", "draft', 'posted")

    op.execute(sa.text("ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'adjustment'"))
    op.execute(sa.text("ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'reversal'"))

    op.add_column(
        "transactions",
        sa.Column(
            "posting_status",
            posting_status,
            nullable=False,
            server_default="posted",
        ),
    )
    op.execute(
        sa.text(
            "UPDATE transactions SET posting_status = 'posted' "
            "WHERE posting_status IS DISTINCT FROM 'posted'"
        )
    )

    op.add_column(
        "transactions",
        sa.Column("reverses_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "transactions",
        sa.Column("reversed_by_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("transactions", sa.Column("correction_reason", sa.Text(), nullable=True))
    op.add_column("transactions", sa.Column("delta_sign", sa.SmallInteger(), nullable=True))

    op.create_check_constraint(
        "ck_transactions_delta_sign",
        "transactions",
        "delta_sign IS NULL OR delta_sign IN (-1, 1)",
    )

    op.create_foreign_key(
        "fk_transactions_reverses_id",
        "transactions",
        "transactions",
        ["reverses_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_transactions_reversed_by_id",
        "transactions",
        "transactions",
        ["reversed_by_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index(
        "ix_transactions_org_posting_status",
        "transactions",
        ["organization_id", "posting_status"],
    )
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_transactions_reversed_by_id "
            "ON transactions (reversed_by_id) WHERE reversed_by_id IS NOT NULL"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_transactions_reverses_id "
            "ON transactions (reverses_id) WHERE reverses_id IS NOT NULL"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_transactions_reverses_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS uq_transactions_reversed_by_id"))
    op.drop_index("ix_transactions_org_posting_status", table_name="transactions")

    op.drop_constraint("fk_transactions_reversed_by_id", "transactions", type_="foreignkey")
    op.drop_constraint("fk_transactions_reverses_id", "transactions", type_="foreignkey")
    op.drop_constraint("ck_transactions_delta_sign", "transactions", type_="check")

    op.drop_column("transactions", "delta_sign")
    op.drop_column("transactions", "correction_reason")
    op.drop_column("transactions", "reversed_by_id")
    op.drop_column("transactions", "reverses_id")
    op.drop_column("transactions", "posting_status")

    op.execute(sa.text("DROP TYPE IF EXISTS posting_status"))
    # Postgres cannot safely remove enum labels; 'adjustment' / 'reversal' remain on
    # transaction_type after downgrade (see docs/GOTCHAS.md).
