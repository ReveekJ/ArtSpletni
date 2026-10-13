"""make latitude and longitude NOT NULL on audio_tracks and checkpoints

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-13

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "DELETE FROM audio_tracks WHERE latitude IS NULL OR longitude IS NULL"
    )
    op.execute(
        "DELETE FROM checkpoints WHERE latitude IS NULL OR longitude IS NULL"
    )
    op.alter_column("audio_tracks", "latitude", existing_type=sa.Float(), nullable=False)
    op.alter_column("audio_tracks", "longitude", existing_type=sa.Float(), nullable=False)
    op.alter_column("checkpoints", "latitude", existing_type=sa.Float(), nullable=False)
    op.alter_column("checkpoints", "longitude", existing_type=sa.Float(), nullable=False)


def downgrade() -> None:
    op.alter_column("checkpoints", "longitude", existing_type=sa.Float(), nullable=True)
    op.alter_column("checkpoints", "latitude", existing_type=sa.Float(), nullable=True)
    op.alter_column("audio_tracks", "longitude", existing_type=sa.Float(), nullable=True)
    op.alter_column("audio_tracks", "latitude", existing_type=sa.Float(), nullable=True)
