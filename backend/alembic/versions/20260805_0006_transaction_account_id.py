"""Add transactions.account_id, backfill, make credit_card_id nullable.

Revision ID: 20260805_0006
Revises: 20260805_0005
Create Date: 2026-08-05
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260805_0006"
down_revision: str | None = "20260805_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.execute(
        sa.text(
            """
            UPDATE transactions t
            SET account_id = a.id
            FROM accounts a
            WHERE a.credit_card_id = t.credit_card_id
              AND t.account_id IS NULL
            """
        )
    )

    conn = op.get_bind()
    remaining = conn.execute(
        sa.text("SELECT count(*) FROM transactions WHERE account_id IS NULL")
    ).scalar()
    if remaining and int(remaining) > 0:
        raise RuntimeError(f"Cannot set account_id NOT NULL: {remaining} transaction(s) still null")

    op.alter_column("transactions", "account_id", nullable=False)
    op.create_foreign_key(
        "fk_transactions_account_id",
        "transactions",
        "accounts",
        ["account_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.alter_column(
        "transactions", "credit_card_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True
    )

    op.create_index("ix_transactions_account_id", "transactions", ["account_id"])
    op.create_index(
        "ix_transactions_org_account",
        "transactions",
        ["organization_id", "account_id"],
    )


def downgrade() -> None:
    conn = op.get_bind()
    null_cards = conn.execute(
        sa.text("SELECT count(*) FROM transactions WHERE credit_card_id IS NULL")
    ).scalar()
    if null_cards and int(null_cards) > 0:
        raise RuntimeError(
            f"Cannot restore credit_card_id NOT NULL: {null_cards} row(s) have null card"
        )

    op.drop_index("ix_transactions_org_account", table_name="transactions")
    op.drop_index("ix_transactions_account_id", table_name="transactions")
    op.drop_constraint("fk_transactions_account_id", "transactions", type_="foreignkey")
    op.alter_column(
        "transactions",
        "credit_card_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.drop_column("transactions", "account_id")
