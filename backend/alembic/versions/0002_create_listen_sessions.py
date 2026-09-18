"""create listen_sessions table

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-18

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "listen_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "track_id",
            sa.Integer(),
            sa.ForeignKey("audio_tracks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_token", sa.String(36), unique=True, nullable=False),
        sa.Column("visitor_id", sa.String(36), nullable=False),
        sa.Column("track_duration_seconds", sa.Float(), nullable=True),
        sa.Column("listened_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_position_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("completion_ratio", sa.Float(), nullable=True),
        sa.Column("seek_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("referrer", sa.String(512), nullable=True),
        sa.Column("language", sa.String(16), nullable=True),
        sa.Column("device_type", sa.String(16), nullable=True),
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
    op.create_index("ix_listen_sessions_track_id", "listen_sessions", ["track_id"])
    op.create_index("ix_listen_sessions_visitor_id", "listen_sessions", ["visitor_id"])
    op.create_index("ix_listen_sessions_created_at", "listen_sessions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_listen_sessions_created_at", table_name="listen_sessions")
    op.drop_index("ix_listen_sessions_visitor_id", table_name="listen_sessions")
    op.drop_index("ix_listen_sessions_track_id", table_name="listen_sessions")
    op.drop_table("listen_sessions")
