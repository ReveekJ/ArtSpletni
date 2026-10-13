"""create routes, checkpoints, route_stops, dependencies, progress tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-12

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "routes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(32), unique=True, nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_s3_key", sa.String(512), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),  # noqa: E501
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),  # noqa: E501
    )

    op.create_table(
        "checkpoints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(32), unique=True, nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("location_name", sa.String(255), nullable=True),
        sa.Column("content_type", sa.String(16), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=True),
        sa.Column("image_s3_key", sa.String(512), nullable=True),
        sa.Column("loot_type", sa.String(16), nullable=True),
        sa.Column("loot_value", sa.Text(), nullable=True),
        sa.Column("audio_s3_key", sa.String(512), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),  # noqa: E501
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),  # noqa: E501
    )

    op.create_table(
        "route_stops",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "route_id",
            sa.Integer(),
            sa.ForeignKey("routes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stop_type", sa.String(16), nullable=False),
        sa.Column(
            "track_id",
            sa.Integer(),
            sa.ForeignKey("audio_tracks.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "checkpoint_id",
            sa.Integer(),
            sa.ForeignKey("checkpoints.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "completion_criteria",
            sa.String(16),
            nullable=False,
            server_default="scan",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),  # noqa: E501
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),  # noqa: E501
        sa.CheckConstraint(
            "(track_id IS NOT NULL) != (checkpoint_id IS NOT NULL)",
            name="ck_route_stops_exactly_one_target",
        ),
    )
    op.create_index("ix_route_stops_route_id", "route_stops", ["route_id"])
    op.create_index("ix_route_stops_track_id", "route_stops", ["track_id"])
    op.create_index("ix_route_stops_checkpoint_id", "route_stops", ["checkpoint_id"])

    op.create_table(
        "route_stop_dependencies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "route_stop_id",
            sa.Integer(),
            sa.ForeignKey("route_stops.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "depends_on_stop_id",
            sa.Integer(),
            sa.ForeignKey("route_stops.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),  # noqa: E501
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),  # noqa: E501
        sa.UniqueConstraint(
            "route_stop_id", "depends_on_stop_id",
            name="uq_route_stop_dependency_pair",
        ),
    )
    op.create_index(
        "ix_route_stop_dependencies_route_stop_id",
        "route_stop_dependencies",
        ["route_stop_id"],
    )
    op.create_index(
        "ix_route_stop_dependencies_depends_on_stop_id",
        "route_stop_dependencies",
        ["depends_on_stop_id"],
    )

    op.create_table(
        "user_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "route_stop_id",
            sa.Integer(),
            sa.ForeignKey("route_stops.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),  # noqa: E501
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),  # noqa: E501
        sa.UniqueConstraint("user_id", "route_stop_id", name="uq_user_progress_stop"),
    )
    op.create_index("ix_user_progress_user_id", "user_progress", ["user_id"])
    op.create_index("ix_user_progress_route_stop_id", "user_progress", ["route_stop_id"])


def downgrade() -> None:
    op.drop_index("ix_user_progress_route_stop_id", table_name="user_progress")
    op.drop_index("ix_user_progress_user_id", table_name="user_progress")
    op.drop_table("user_progress")
    op.drop_index(
        "ix_route_stop_dependencies_depends_on_stop_id",
        table_name="route_stop_dependencies",
    )
    op.drop_index(
        "ix_route_stop_dependencies_route_stop_id",
        table_name="route_stop_dependencies",
    )
    op.drop_table("route_stop_dependencies")
    op.drop_index("ix_route_stops_checkpoint_id", table_name="route_stops")
    op.drop_index("ix_route_stops_track_id", table_name="route_stops")
    op.drop_index("ix_route_stops_route_id", table_name="route_stops")
    op.drop_table("route_stops")
    op.drop_table("checkpoints")
    op.drop_table("routes")
