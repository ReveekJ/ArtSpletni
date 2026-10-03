"""create browser-bound track access grants

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-03

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "track_access_grants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "track_id",
            sa.Integer(),
            sa.ForeignKey("audio_tracks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("secret_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
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
    )
    op.create_index("ix_track_access_grants_track_id", "track_access_grants", ["track_id"])
    op.create_index("ix_track_access_grants_secret_hash", "track_access_grants", ["secret_hash"])
    op.create_index("ix_track_access_grants_expires_at", "track_access_grants", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_track_access_grants_expires_at", table_name="track_access_grants")
    op.drop_index("ix_track_access_grants_secret_hash", table_name="track_access_grants")
    op.drop_index("ix_track_access_grants_track_id", table_name="track_access_grants")
    op.drop_table("track_access_grants")