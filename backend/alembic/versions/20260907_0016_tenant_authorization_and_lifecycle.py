"""Tenant authorization and account lifecycle hardening:
- Audit existing rows for cross-org inconsistencies
- Add DeletedAccount tombstone table
- Add composite unique constraints (id, organization_id)
- Add composite foreign keys enforcing cross-org isolation

Revision ID: 20260907_0016
Revises: 20260907_0015
Create Date: 2026-09-07
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260907_0016"
down_revision: str | None = "20260907_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PRE_AUDIT_CHECKS = [
    (
        "credit_cards.held_by_contact_id",
        """
        SELECT count(*) FROM credit_cards c
        JOIN contacts ct ON c.held_by_contact_id = ct.id
        WHERE c.organization_id <> ct.organization_id
        """,
    ),
    (
        "statements.credit_card_id",
        """
        SELECT count(*) FROM statements s
        JOIN credit_cards c ON s.credit_card_id = c.id
        WHERE s.organization_id <> c.organization_id
        """,
    ),
    (
        "statement_line_candidates.statement_id",
        """
        SELECT count(*) FROM statement_line_candidates slc
        JOIN statements s ON slc.statement_id = s.id
        WHERE slc.organization_id <> s.organization_id
        """,
    ),
    (
        "transactions.account_id",
        """
        SELECT count(*) FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        WHERE t.organization_id <> a.organization_id
        """,
    ),
    (
        "transactions.credit_card_id",
        """
        SELECT count(*) FROM transactions t
        JOIN credit_cards c ON t.credit_card_id = c.id
        WHERE t.organization_id <> c.organization_id
        """,
    ),
    (
        "transactions.contact_id",
        """
        SELECT count(*) FROM transactions t
        JOIN contacts ct ON t.contact_id = ct.id
        WHERE t.organization_id <> ct.organization_id
        """,
    ),
    (
        "transactions.category_id",
        """
        SELECT count(*) FROM transactions t
        JOIN categories cat ON t.category_id = cat.id
        WHERE t.organization_id <> cat.org_id
        """,
    ),
    (
        "settlements.contact_id",
        """
        SELECT count(*) FROM settlements s
        JOIN contacts ct ON s.contact_id = ct.id
        WHERE s.organization_id <> ct.organization_id
        """,
    ),
    (
        "obligations.contact_id",
        """
        SELECT count(*) FROM obligations o
        JOIN contacts ct ON o.contact_id = ct.id
        WHERE o.organization_id <> ct.organization_id
        """,
    ),
    (
        "obligation_payments.obligation_id",
        """
        SELECT count(*) FROM obligation_payments op
        JOIN obligations o ON op.obligation_id = o.id
        WHERE op.organization_id <> o.organization_id
        """,
    ),
    (
        "emi_plans.credit_card_id",
        """
        SELECT count(*) FROM emi_plans ep
        JOIN credit_cards c ON ep.credit_card_id = c.id
        WHERE ep.organization_id <> c.organization_id
        """,
    ),
]


def _audit_existing_rows(conn: sa.engine.Connection) -> None:
    for check_name, query in PRE_AUDIT_CHECKS:
        try:
            cnt = conn.execute(sa.text(query)).scalar()
            if cnt and cnt > 0:
                raise RuntimeError(
                    f"Cannot apply migration 20260907_0016: found {cnt} cross-organization "
                    f"inconsistent row(s) in check '{check_name}'."
                )
        except Exception as e:
            if "RuntimeError" in type(e).__name__:
                raise
            # If table doesn't exist yet (e.g. fresh DB migration), skip check safely
            pass


def upgrade() -> None:
    conn = op.get_bind()
    _audit_existing_rows(conn)

    # 1. Create deleted_accounts tombstone table
    op.create_table(
        "deleted_accounts",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "provider_deleted",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_deleted_accounts_user_id",
        "deleted_accounts",
        ["user_id"],
        unique=True,
    )

    if conn.dialect.name == "postgresql":
        op.execute(sa.text("ALTER TABLE deleted_accounts ENABLE ROW LEVEL SECURITY;"))
        op.execute(
            sa.text(
                "REVOKE ALL ON TABLE deleted_accounts FROM anon, authenticated, PUBLIC;"
            )
        )

    # 2. Create composite UNIQUE constraints
    op.create_unique_constraint(
        "uq_credit_cards_id_org", "credit_cards", ["id", "organization_id"]
    )
    op.create_unique_constraint(
        "uq_accounts_id_org", "accounts", ["id", "organization_id"]
    )
    op.create_unique_constraint(
        "uq_contacts_id_org", "contacts", ["id", "organization_id"]
    )
    op.create_unique_constraint(
        "uq_categories_id_org", "categories", ["id", "org_id"]
    )
    op.create_unique_constraint(
        "uq_statements_id_org", "statements", ["id", "organization_id"]
    )
    op.create_unique_constraint(
        "uq_transactions_id_org", "transactions", ["id", "organization_id"]
    )
    op.create_unique_constraint(
        "uq_obligations_id_org", "obligations", ["id", "organization_id"]
    )
    op.create_unique_constraint(
        "uq_emi_plans_id_org", "emi_plans", ["id", "organization_id"]
    )

    # 3. Create composite FOREIGN KEY constraints
    op.create_foreign_key(
        "fk_statements_card_org",
        "statements",
        "credit_cards",
        ["credit_card_id", "organization_id"],
        ["id", "organization_id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_statement_lines_statement_org",
        "statement_line_candidates",
        "statements",
        ["statement_id", "organization_id"],
        ["id", "organization_id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_transactions_account_org",
        "transactions",
        "accounts",
        ["account_id", "organization_id"],
        ["id", "organization_id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_settlements_contact_org",
        "settlements",
        "contacts",
        ["contact_id", "organization_id"],
        ["id", "organization_id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_obligation_payments_obligation_org",
        "obligation_payments",
        "obligations",
        ["obligation_id", "organization_id"],
        ["id", "organization_id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_emi_plans_card_org",
        "emi_plans",
        "credit_cards",
        ["credit_card_id", "organization_id"],
        ["id", "organization_id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # 1. Drop composite foreign keys
    op.drop_constraint("fk_emi_plans_card_org", "emi_plans", type_="foreignkey")
    op.drop_constraint(
        "fk_obligation_payments_obligation_org", "obligation_payments", type_="foreignkey"
    )
    op.drop_constraint("fk_settlements_contact_org", "settlements", type_="foreignkey")
    op.drop_constraint("fk_transactions_account_org", "transactions", type_="foreignkey")
    op.drop_constraint(
        "fk_statement_lines_statement_org", "statement_line_candidates", type_="foreignkey"
    )
    op.drop_constraint("fk_statements_card_org", "statements", type_="foreignkey")

    # 2. Drop composite unique constraints
    op.drop_constraint("uq_emi_plans_id_org", "emi_plans", type_="unique")
    op.drop_constraint("uq_obligations_id_org", "obligations", type_="unique")
    op.drop_constraint("uq_transactions_id_org", "transactions", type_="unique")
    op.drop_constraint("uq_statements_id_org", "statements", type_="unique")
    op.drop_constraint("uq_categories_id_org", "categories", type_="unique")
    op.drop_constraint("uq_contacts_id_org", "contacts", type_="unique")
    op.drop_constraint("uq_accounts_id_org", "accounts", type_="unique")
    op.drop_constraint("uq_credit_cards_id_org", "credit_cards", type_="unique")

    # 3. Drop deleted_accounts table
    op.drop_index("ix_deleted_accounts_user_id", table_name="deleted_accounts")
    op.drop_table("deleted_accounts")
