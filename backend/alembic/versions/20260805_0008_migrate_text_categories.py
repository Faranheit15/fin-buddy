"""migrate text categories

Revision ID: d01947b0fa9e
Revises: 20260805_0007
Create Date: 2026-08-05 23:14:36.378040

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd01947b0fa9e'
down_revision: Union[str, Sequence[str], None] = '20260805_0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


import uuid
from datetime import datetime, timezone

def upgrade() -> None:
    conn = op.get_bind()
    
    # Get all distinct (organization_id, category) pairs from transactions
    # where category_id IS NULL AND category IS NOT NULL
    results = conn.execute(
        sa.text("SELECT DISTINCT organization_id, category FROM transactions WHERE category_id IS NULL AND category IS NOT NULL")
    ).fetchall()
    
    if not results:
        return
        
    for org_id, category_text in results:
        if not category_text or not category_text.strip():
            continue
            
        c_text = category_text.strip()
        
        # Check if category exists (case-insensitive)
        row = conn.execute(
            sa.text("SELECT id FROM categories WHERE organization_id = :org_id AND lower(name) = lower(:name)"),
            {"org_id": org_id, "name": c_text}
        ).fetchone()
        
        if row:
            cat_id = row[0]
        else:
            cat_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            conn.execute(
                sa.text("""
                    INSERT INTO categories (id, organization_id, name, kind, created_at, updated_at)
                    VALUES (:id, :org_id, :name, 'expense', :now, :now)
                """),
                {
                    "id": cat_id,
                    "org_id": org_id,
                    "name": c_text,
                    "now": now
                }
            )
            
        # Update transactions for this org and this category
        conn.execute(
            sa.text("""
                UPDATE transactions 
                SET category_id = :cat_id 
                WHERE organization_id = :org_id 
                  AND category = :category_text 
                  AND category_id IS NULL
            """),
            {"cat_id": cat_id, "org_id": org_id, "category_text": category_text}
        )

def downgrade() -> None:
    pass
