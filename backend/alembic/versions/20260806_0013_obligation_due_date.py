"""Add due_date to obligations.

Revision ID: 20260806_0013
Revises: 20260806_0012
"""

import sqlalchemy as sa
from alembic import op

revision = "20260806_0013"
down_revision = "20260806_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("obligations", sa.Column("due_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("obligations", "due_date")
