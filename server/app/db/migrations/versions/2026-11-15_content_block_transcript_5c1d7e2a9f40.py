"""content block transcript

Revision ID: 5c1d7e2a9f40
Revises: 0b21eb741013
Create Date: 2026-11-15 18:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

__all__ = ("downgrade", "upgrade")

revision = "5c1d7e2a9f40"
down_revision = "0b21eb741013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("content_blocks", schema=None) as batch_op:
        batch_op.add_column(sa.Column("transcript", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("content_blocks", schema=None) as batch_op:
        batch_op.drop_column("transcript")
