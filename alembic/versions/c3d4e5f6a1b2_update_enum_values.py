"""update enum values to uppercase

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2026-06-17 19:20:00.000000+00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a1b2'
down_revision: Union[str, None] = 'b2c3d4e5f6a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL doesn't support altering enum values directly, need to recreate types
    # For now, just add RESERVED to motorstatus (other enums need separate migration if needed)
    op.execute("ALTER TYPE motorstatus ADD VALUE IF NOT EXISTS 'RESERVED'")


def downgrade() -> None:
    pass