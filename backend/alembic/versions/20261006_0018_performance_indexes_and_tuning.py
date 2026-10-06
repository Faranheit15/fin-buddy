"""Database and API performance: missing foreign-key indexes and cleanup.

- Add indexes for unindexed single-column and composite foreign keys
- Remove redundant duplicate index on deleted_accounts(user_id)

Revision ID: 20261006_0018
Revises: 20260908_0017
Create Date: 2026-10-06
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20261006_0018"
down_revision: str | None = "20260908_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


NEW_INDEXES = [
    # Single-column foreign keys
    ("ix_credit_cards_held_by_contact_id", "credit_cards", ["held_by_contact_id"]),
    ("ix_emi_plans_reference_transaction_id", "emi_plans", ["reference_transaction_id"]),
    ("ix_obligation_payments_created_by", "obligation_payments", ["created_by"]),
    ("ix_obligations_created_by", "obligations", ["created_by"]),
    ("ix_settlements_created_by", "settlements", ["created_by"]),
    (
        "ix_statement_line_candidates_proposed_contact_id",
        "statement_line_candidates",
        ["proposed_contact_id"],
    ),
    ("ix_statements_created_by", "statements", ["created_by"]),
    ("ix_transactions_created_by", "transactions", ["created_by"]),
    ("ix_transactions_reversed_by_id", "transactions", ["reversed_by_id"]),
    # Composite tenant foreign keys matching (fk_col, organization_id)
    ("ix_statements_card_org", "statements", ["credit_card_id", "organization_id"]),
    (
        "ix_statement_lines_statement_org",
        "statement_line_candidates",
        ["statement_id", "organization_id"],
    ),
    ("ix_transactions_account_org", "transactions", ["account_id", "organization_id"]),
    ("ix_settlements_contact_org", "settlements", ["contact_id", "organization_id"]),
    (
        "ix_obligation_payments_obligation_org",
        "obligation_payments",
        ["obligation_id", "organization_id"],
    ),
    ("ix_emi_plans_card_org", "emi_plans", ["credit_card_id", "organization_id"]),
]


def upgrade() -> None:
    # 1. Add indexes for missing foreign keys
    for index_name, table_name, columns in NEW_INDEXES:
        op.create_index(index_name, table_name, columns, unique=False)

    # 2. Drop duplicate index on deleted_accounts(user_id);
    # unique constraint deleted_accounts_user_id_key already maintains the unique btree index.
    op.drop_index("ix_deleted_accounts_user_id", table_name="deleted_accounts")


def downgrade() -> None:
    # 1. Recreate duplicate index on deleted_accounts
    op.create_index(
        "ix_deleted_accounts_user_id",
        "deleted_accounts",
        ["user_id"],
        unique=True,
    )

    # 2. Drop added foreign key indexes
    for index_name, table_name, _ in reversed(NEW_INDEXES):
        op.drop_index(index_name, table_name=table_name)
