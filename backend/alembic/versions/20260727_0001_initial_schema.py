"""initial schema

Revision ID: 20260727_0001
Revises:
Create Date: 2026-07-27

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260727_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# postgresql.ENUM + create_type=False: never auto-CREATE TYPE on create_table.
# Types are created with IF NOT EXISTS / exception handlers below.
platform_role = postgresql.ENUM(
    "user", "admin", "super_admin", name="platform_role", create_type=False
)
org_role = postgresql.ENUM("owner", "admin", "member", name="org_role", create_type=False)
card_network = postgresql.ENUM(
    "visa", "mastercard", "rupay", "amex", "other", name="card_network", create_type=False
)
due_rule_type = postgresql.ENUM(
    "fixed_day", "days_after_statement", name="due_rule_type", create_type=False
)
card_status = postgresql.ENUM("active", "closed", name="card_status", create_type=False)
transaction_type = postgresql.ENUM(
    "purchase",
    "refund",
    "fee",
    "interest",
    "payment_to_issuer",
    "opening_balance",
    name="transaction_type",
    create_type=False,
)
settlement_method = postgresql.ENUM(
    "upi", "cash", "bank_transfer", "other", name="settlement_method", create_type=False
)
statement_status = postgresql.ENUM(
    "uploaded",
    "parsing",
    "needs_review",
    "imported",
    "failed",
    name="statement_status",
    create_type=False,
)
line_review_status = postgresql.ENUM(
    "pending",
    "accepted",
    "rejected",
    "edited",
    name="line_review_status",
    create_type=False,
)
activity_action = postgresql.ENUM(
    "login",
    "logout",
    "signup",
    "token_refresh",
    "profile_update",
    "org_create",
    "org_update",
    "member_invite",
    "member_update",
    "member_remove",
    "card_create",
    "card_update",
    "card_archive",
    "contact_create",
    "contact_update",
    "contact_archive",
    "transaction_create",
    "transaction_update",
    "transaction_delete",
    "settlement_create",
    "settlement_update",
    "settlement_delete",
    "statement_upload",
    "statement_review",
    "statement_import",
    "notification_read",
    "admin_view",
    "admin_action",
    "api_request",
    "other",
    name="activity_action",
    create_type=False,
)
error_severity = postgresql.ENUM(
    "debug", "info", "warning", "error", "critical", name="error_severity", create_type=False
)

_ENUM_DDL: list[tuple[str, str]] = [
    ("platform_role", "user', 'admin', 'super_admin"),
    ("org_role", "owner', 'admin', 'member"),
    ("card_network", "visa', 'mastercard', 'rupay', 'amex', 'other"),
    ("due_rule_type", "fixed_day', 'days_after_statement"),
    ("card_status", "active', 'closed"),
    (
        "transaction_type",
        "purchase', 'refund', 'fee', 'interest', 'payment_to_issuer', 'opening_balance",
    ),
    ("settlement_method", "upi', 'cash', 'bank_transfer', 'other"),
    ("statement_status", "uploaded', 'parsing', 'needs_review', 'imported', 'failed"),
    ("line_review_status", "pending', 'accepted', 'rejected', 'edited"),
    (
        "activity_action",
        "login', 'logout', 'signup', 'token_refresh', 'profile_update', "
        "'org_create', 'org_update', 'member_invite', 'member_update', 'member_remove', "
        "'card_create', 'card_update', 'card_archive', 'contact_create', 'contact_update', "
        "'contact_archive', 'transaction_create', 'transaction_update', 'transaction_delete', "
        "'settlement_create', 'settlement_update', 'settlement_delete', 'statement_upload', "
        "'statement_review', 'statement_import', 'notification_read', 'admin_view', "
        "'admin_action', 'api_request', 'other",
    ),
    ("error_severity", "debug', 'info', 'warning', 'error', 'critical"),
]


def _ensure_enum(name: str, values_sql: str) -> None:
    """Create a Postgres enum if missing (safe to re-run after partial upgrades)."""
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
    for name, values_sql in _ENUM_DDL:
        _ensure_enum(name, values_sql)

    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("display_name", sa.String(length=200), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Asia/Kolkata"),
        sa.Column(
            "platform_role",
            platform_role,
            nullable=False,
            server_default="user",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
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
    )
    op.create_index("ix_profiles_email", "profiles", ["email"])
    op.create_index("ix_profiles_phone", "profiles", ["phone"])

    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
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
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])

    op.create_table(
        "organization_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", org_role, nullable=False),
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
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
    )
    op.create_index(
        "ix_organization_members_organization_id", "organization_members", ["organization_id"]
    )
    op.create_index("ix_organization_members_user_id", "organization_members", ["user_id"])

    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String(length=64)), nullable=True),
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
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_contacts_organization_id", "contacts", ["organization_id"])

    op.create_table(
        "credit_cards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nickname", sa.String(length=120), nullable=False),
        sa.Column("issuer", sa.String(length=120), nullable=False),
        sa.Column("network", card_network, nullable=False),
        sa.Column("last_four", sa.String(length=4), nullable=False),
        sa.Column("credit_limit_paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("statement_day", sa.Integer(), nullable=False),
        sa.Column("due_rule_type", due_rule_type, nullable=False),
        sa.Column("due_rule_value", sa.Integer(), nullable=False),
        sa.Column("status", card_status, nullable=False, server_default="active"),
        sa.Column("held_by_contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["held_by_contact_id"], ["contacts.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_credit_cards_organization_id", "credit_cards", ["organization_id"])

    op.create_table(
        "statements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("credit_card_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("statement_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("pdf_storage_path", sa.Text(), nullable=True),
        sa.Column("status", statement_status, nullable=False, server_default="uploaded"),
        sa.Column("parse_error", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["credit_card_id"], ["credit_cards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["profiles.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_statements_organization_id", "statements", ["organization_id"])
    op.create_index("ix_statements_credit_card_id", "statements", ["credit_card_id"])

    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("credit_card_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("statement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("type", transaction_type, nullable=False),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("merchant", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
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
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["credit_card_id"], ["credit_cards.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["statement_id"], ["statements.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["profiles.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_transactions_organization_id", "transactions", ["organization_id"])
    op.create_index("ix_transactions_credit_card_id", "transactions", ["credit_card_id"])
    op.create_index("ix_transactions_contact_id", "transactions", ["contact_id"])
    op.create_index("ix_transactions_statement_id", "transactions", ["statement_id"])
    op.create_index("ix_transactions_occurred_at", "transactions", ["occurred_at"])

    op.create_table(
        "statement_line_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("statement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("merchant", sa.String(length=255), nullable=True),
        sa.Column("amount_paise", sa.BigInteger(), nullable=True),
        sa.Column("proposed_type", transaction_type, nullable=True),
        sa.Column("proposed_contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("review_status", line_review_status, nullable=False, server_default="pending"),
        sa.Column("committed_transaction_id", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(["statement_id"], ["statements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["proposed_contact_id"], ["contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["committed_transaction_id"], ["transactions.id"], ondelete="SET NULL"
        ),
    )
    op.create_index(
        "ix_statement_line_candidates_statement_id", "statement_line_candidates", ["statement_id"]
    )
    op.create_index(
        "ix_statement_line_candidates_organization_id",
        "statement_line_candidates",
        ["organization_id"],
    )

    op.create_table(
        "settlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("method", settlement_method, nullable=False),
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
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["profiles.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_settlements_organization_id", "settlements", ["organization_id"])
    op.create_index("ix_settlements_contact_id", "settlements", ["contact_id"])
    op.create_index("ix_settlements_settled_at", "settlements", ["settled_at"])

    op.create_table(
        "in_app_notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("href", sa.String(length=500), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_in_app_notifications_organization_id", "in_app_notifications", ["organization_id"]
    )
    op.create_index("ix_in_app_notifications_user_id", "in_app_notifications", ["user_id"])
    op.create_index("ix_in_app_notifications_created_at", "in_app_notifications", ["created_at"])

    op.create_table(
        "activity_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", activity_action, nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=True),
        sa.Column("resource_id", sa.String(length=80), nullable=True),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_activity_logs_actor_user_id", "activity_logs", ["actor_user_id"])
    op.create_index("ix_activity_logs_organization_id", "activity_logs", ["organization_id"])
    op.create_index("ix_activity_logs_action", "activity_logs", ["action"])
    op.create_index("ix_activity_logs_resource_type", "activity_logs", ["resource_type"])
    op.create_index("ix_activity_logs_created_at", "activity_logs", ["created_at"])

    op.create_table(
        "error_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("severity", error_severity, nullable=False),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("exception_type", sa.String(length=200), nullable=True),
        sa.Column("stack_trace", sa.Text(), nullable=True),
        sa.Column("path", sa.String(length=500), nullable=True),
        sa.Column("method", sa.String(length=16), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_error_logs_actor_user_id", "error_logs", ["actor_user_id"])
    op.create_index("ix_error_logs_organization_id", "error_logs", ["organization_id"])
    op.create_index("ix_error_logs_severity", "error_logs", ["severity"])
    op.create_index("ix_error_logs_error_code", "error_logs", ["error_code"])
    op.create_index("ix_error_logs_request_id", "error_logs", ["request_id"])
    op.create_index("ix_error_logs_created_at", "error_logs", ["created_at"])

    op.create_table(
        "api_request_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("method", sa.String(length=16), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("query_string", sa.Text(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("request_body", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["profiles.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_api_request_logs_request_id", "api_request_logs", ["request_id"])
    op.create_index("ix_api_request_logs_actor_user_id", "api_request_logs", ["actor_user_id"])
    op.create_index("ix_api_request_logs_path", "api_request_logs", ["path"])
    op.create_index("ix_api_request_logs_status_code", "api_request_logs", ["status_code"])
    op.create_index("ix_api_request_logs_created_at", "api_request_logs", ["created_at"])

    op.create_table(
        "seed_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("seed_name", sa.String(length=120), nullable=False),
        sa.Column(
            "applied_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("checksum", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("seed_name"),
    )


def downgrade() -> None:
    op.drop_table("seed_history")
    op.drop_table("api_request_logs")
    op.drop_table("error_logs")
    op.drop_table("activity_logs")
    op.drop_table("in_app_notifications")
    op.drop_table("settlements")
    op.drop_table("statement_line_candidates")
    op.drop_table("transactions")
    op.drop_table("statements")
    op.drop_table("credit_cards")
    op.drop_table("contacts")
    op.drop_table("organization_members")
    op.drop_table("organizations")
    op.drop_table("profiles")

    for name, _values in reversed(_ENUM_DDL):
        op.execute(sa.text(f"DROP TYPE IF EXISTS {name}"))
