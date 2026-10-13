"""create track localizations table

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-13

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "track_localizations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "track_id",
            sa.Integer,
            sa.ForeignKey("audio_tracks.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("language", sa.String(2), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("location_name", sa.String(255), nullable=True),
        sa.Column("audio_s3_key", sa.String(512), nullable=True),
        sa.Column("cover_s3_key", sa.String(512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "track_id",
            "language",
            name="uq_track_localizations_track_language",
        ),
    )


def downgrade() -> None:
    op.drop_table("track_localizations")
