"""Add activity_action values for ledger post / reverse / adjust.

Revision ID: 20260805_0004
Revises: 20260805_0003
Create Date: 2026-08-05
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260805_0004"
down_revision: str | None = "20260805_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TYPE activity_action ADD VALUE IF NOT EXISTS 'transaction_post'"))
    op.execute(sa.text("ALTER TYPE activity_action ADD VALUE IF NOT EXISTS 'transaction_reverse'"))
    op.execute(sa.text("ALTER TYPE activity_action ADD VALUE IF NOT EXISTS 'transaction_adjust'"))


def downgrade() -> None:
    # Postgres cannot safely remove enum labels; values remain after downgrade.
    pass
