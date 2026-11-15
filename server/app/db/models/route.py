from datetime import datetime
from enum import StrEnum
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.types import str_enum
from app.lib.i18n import LocalizedText, LocalizedTextType


class OrderingMode(StrEnum):
    FREE = "free"
    SEQUENTIAL = "sequential"
    GRAPH = "graph"


class MapVisibility(StrEnum):
    ALL = "all"
    PROGRESSIVE = "progressive"
    VISITED_WITH_HINTS = "visited_with_hints"


class RouteStopDependency(UUIDv7AuditBase):
    __tablename__ = "route_stop_dependencies"
    __table_args__ = (
        UniqueConstraint("stop_id", "depends_on_stop_id"),
        CheckConstraint("stop_id <> depends_on_stop_id", name="no_self_dependency"),
    )

    stop_id: Mapped[UUID] = mapped_column(ForeignKey("route_stops.id", ondelete="CASCADE"), index=True)
    depends_on_stop_id: Mapped[UUID] = mapped_column(
        ForeignKey("route_stops.id", ondelete="CASCADE"), index=True
    )


class RouteStop(UUIDv7AuditBase):
    __tablename__ = "route_stops"
    __table_args__ = (UniqueConstraint("route_id", "point_id"),)

    route_id: Mapped[UUID] = mapped_column(ForeignKey("routes.id", ondelete="CASCADE"), index=True)
    point_id: Mapped[UUID] = mapped_column(ForeignKey("points.id", ondelete="RESTRICT"), index=True)
    position: Mapped[int]
    is_start: Mapped[bool] = mapped_column(default=False)
    is_required: Mapped[bool] = mapped_column(default=True)
    hint: Mapped[LocalizedText | None] = mapped_column(LocalizedTextType(), default=None)
    graph_x: Mapped[float | None] = mapped_column(default=None)
    graph_y: Mapped[float | None] = mapped_column(default=None)
    dependencies: Mapped[list[RouteStopDependency]] = relationship(
        foreign_keys=[RouteStopDependency.stop_id],
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Route(UUIDv7AuditBase):
    __tablename__ = "routes"

    slug: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[LocalizedText] = mapped_column(LocalizedTextType())
    description: Mapped[LocalizedText | None] = mapped_column(LocalizedTextType(), default=None)
    cover_asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("media_assets.id", ondelete="SET NULL"), default=None
    )
    ordering_mode: Mapped[OrderingMode] = mapped_column(str_enum(OrderingMode), default=OrderingMode.FREE)
    map_visibility: Mapped[MapVisibility] = mapped_column(str_enum(MapVisibility), default=MapVisibility.ALL)
    active_from: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), default=None)
    active_until: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), default=None)
    is_repeatable: Mapped[bool] = mapped_column(default=False)
    is_published: Mapped[bool] = mapped_column(default=False)
    stops: Mapped[list[RouteStop]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="RouteStop.position"
    )

    def is_active_at(self, moment: datetime) -> bool:
        if self.active_from is not None and moment < self.active_from:
            return False
        return self.active_until is None or moment < self.active_until
