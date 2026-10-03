"""add moderation status to audio tracks

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-03

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "audio_tracks",
        sa.Column("moderation_status", sa.String(16), nullable=True),
    )
    op.execute(
        "UPDATE audio_tracks SET moderation_status = CASE "
        "WHEN is_published THEN 'published' ELSE 'pending' END"
    )
    op.alter_column("audio_tracks", "moderation_status", nullable=False, server_default="pending")
    op.create_index(
        "ix_audio_tracks_moderation_status", "audio_tracks", ["moderation_status"]
    )


def downgrade() -> None:
    op.drop_index("ix_audio_tracks_moderation_status", table_name="audio_tracks")
    op.drop_column("audio_tracks", "moderation_status")