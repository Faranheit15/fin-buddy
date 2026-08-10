"""Create shared rate-limit windows.

Revision ID: 20260810_0014
Revises: 20260806_0013
"""

import sqlalchemy as sa
from alembic import op

revision = "20260810_0014"
down_revision = "20260806_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rate_limit_windows",
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("bucket", sa.String(length=80), nullable=False),
        sa.Column("hit_count", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("key_hash"),
    )
    op.create_index("ix_rate_limit_windows_bucket", "rate_limit_windows", ["bucket"])
    op.create_index("ix_rate_limit_windows_expires_at", "rate_limit_windows", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_rate_limit_windows_expires_at", table_name="rate_limit_windows")
    op.drop_index("ix_rate_limit_windows_bucket", table_name="rate_limit_windows")
    op.drop_table("rate_limit_windows")
