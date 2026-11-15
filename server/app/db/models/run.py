from datetime import datetime
from enum import StrEnum
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.types import str_enum


class RunStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class StopVisit(UUIDv7AuditBase):
    __tablename__ = "stop_visits"
    __table_args__ = (UniqueConstraint("run_id", "stop_id"),)

    run_id: Mapped[UUID] = mapped_column(ForeignKey("route_runs.id", ondelete="CASCADE"), index=True)
    stop_id: Mapped[UUID] = mapped_column(ForeignKey("route_stops.id", ondelete="CASCADE"), index=True)


class RouteRun(UUIDv7AuditBase):
    __tablename__ = "route_runs"
    __table_args__ = (
        Index(
            "uq_route_runs_one_active_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    route_id: Mapped[UUID] = mapped_column(ForeignKey("routes.id", ondelete="CASCADE"), index=True)
    status: Mapped[RunStatus] = mapped_column(str_enum(RunStatus), default=RunStatus.ACTIVE)
    completed_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), default=None)
    visits: Mapped[list[StopVisit]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="StopVisit.created_at"
    )

    @property
    def visited_stop_ids(self) -> set[UUID]:
        return {visit.stop_id for visit in self.visits}
