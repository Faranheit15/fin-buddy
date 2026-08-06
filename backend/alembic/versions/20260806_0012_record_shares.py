"""record_shares migration

Revision ID: 20260806_0012
Revises: 20260806_0011
Create Date: 2026-08-06 14:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260806_0012"
down_revision: str | Sequence[str] | None = "20260806_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

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
    op.create_table(
        "record_shares",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("record_type", sa.String(length=64), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shared_with_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shared_with_user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_record_shares_org_type_record",
        "record_shares",
        ["organization_id", "record_type", "record_id"],
        unique=False,
    )
    op.create_index(
        "ix_record_shares_shared_with",
        "record_shares",
        ["shared_with_user_id"],
        unique=False,
    )

    op.execute(sa.text("ALTER TABLE record_shares ENABLE ROW LEVEL SECURITY"))

    if _auth_uid_exists():
        op.execute(
            sa.text(
                """
                CREATE POLICY record_shares_select ON record_shares
                  FOR SELECT USING (
                    shared_with_user_id = auth.uid() OR
                    organization_id IN (
                      SELECT organization_id FROM organization_members WHERE user_id = auth.uid()
                    )
                  )
                """
            )
        )


def downgrade() -> None:
    if _auth_uid_exists():
        op.execute(sa.text("DROP POLICY IF EXISTS record_shares_select ON record_shares"))
    op.execute(sa.text("ALTER TABLE record_shares DISABLE ROW LEVEL SECURITY"))
    
    op.drop_index("ix_record_shares_shared_with", table_name="record_shares")
    op.drop_index("ix_record_shares_org_type_record", table_name="record_shares")
    op.drop_table("record_shares")
