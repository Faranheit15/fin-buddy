"""email_reminders_enabled

Revision ID: 20260806_0011
Revises: 20260806_0010
Create Date: 2026-08-06 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260806_0011"
down_revision: str | Sequence[str] | None = "20260806_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column(
            "email_reminders_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="true"
        )
    )


def downgrade() -> None:
    op.drop_column("profiles", "email_reminders_enabled")
