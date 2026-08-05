"""Add categories, splits, and transfers.

Revision ID: 20260805_0007
Revises: 20260805_0006
Create Date: 2026-08-05
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260805_0007"
down_revision: str | None = "20260805_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

category_kind = postgresql.ENUM(
    "income",
    "expense",
    name="category_kind",
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
    _ensure_enum("category_kind", "income', 'expense")

    op.execute(sa.text("ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'transfer_out'"))
    op.execute(sa.text("ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'transfer_in'"))

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("kind", category_kind, nullable=False),
        sa.Column("color", sa.String(length=30), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=True),
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
            ["org_id"],
            ["organizations.id"],
            name="fk_categories_org_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_categories"),
    )
    op.create_index(
        "ix_categories_org_id",
        "categories",
        ["org_id"],
        unique=False,
    )

    op.add_column(
        "transactions",
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "transactions",
        sa.Column("transfer_group_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "transactions",
        sa.Column("tags", postgresql.ARRAY(sa.String(length=50)), nullable=True),
    )
    op.create_foreign_key(
        "fk_transactions_category_id",
        "transactions",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_transactions_category_id",
        "transactions",
        ["category_id"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_transfer_group_id",
        "transactions",
        ["transfer_group_id"],
        unique=False,
    )

    op.create_table(
        "transaction_splits",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("amount_paise", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String(length=50)), nullable=True),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name="fk_transaction_splits_category_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            name="fk_transaction_splits_transaction_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_transaction_splits"),
    )
    op.create_index(
        "ix_transaction_splits_transaction_id",
        "transaction_splits",
        ["transaction_id"],
        unique=False,
    )
    op.create_index(
        "ix_transaction_splits_category_id",
        "transaction_splits",
        ["category_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_transaction_splits_category_id", table_name="transaction_splits")
    op.drop_index("ix_transaction_splits_transaction_id", table_name="transaction_splits")
    op.drop_table("transaction_splits")

    op.drop_index("ix_transactions_transfer_group_id", table_name="transactions")
    op.drop_index("ix_transactions_category_id", table_name="transactions")
    op.drop_constraint("fk_transactions_category_id", "transactions", type_="foreignkey")
    op.drop_column("transactions", "tags")
    op.drop_column("transactions", "transfer_group_id")
    op.drop_column("transactions", "category_id")

    op.drop_index("ix_categories_org_id", table_name="categories")
    op.drop_table("categories")
    op.execute(sa.text("DROP TYPE IF EXISTS category_kind"))
