"""Add notification preference thresholds on profiles.

Revision ID: 20260728_0002
Revises: 20260727_0001
Create Date: 2026-07-28
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260728_0002"
down_revision: str | None = "20260727_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column(
            "due_soon_days",
            sa.Integer(),
            nullable=False,
            server_default="7",
        ),
    )
    op.add_column(
        "profiles",
        sa.Column(
            "high_utilization_percent",
            sa.Integer(),
            nullable=False,
            server_default="80",
        ),
    )


def downgrade() -> None:
    op.drop_column("profiles", "high_utilization_percent")
    op.drop_column("profiles", "due_soon_days")
