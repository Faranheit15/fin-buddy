"""add_gst_paise_to_transactions

Revision ID: 20260806_0010
Revises: 20260806_0009
Create Date: 2026-08-06 12:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260806_0010"
down_revision: str | Sequence[str] | None = "20260806_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("gst_paise", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("transactions", "gst_paise")
