from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.entities.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.entities.route import Route


class RouteStop(Base, TimestampMixin):
    __tablename__ = "route_stops"
    __table_args__ = (
        CheckConstraint(
            "(track_id IS NOT NULL) != (checkpoint_id IS NOT NULL)",
            name="ck_route_stops_exactly_one_target",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    route_id: Mapped[int] = mapped_column(
        ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stop_type: Mapped[str] = mapped_column(String(16), nullable=False)
    track_id: Mapped[int | None] = mapped_column(
        ForeignKey("audio_tracks.id", ondelete="CASCADE"), nullable=True,
    )
    checkpoint_id: Mapped[int | None] = mapped_column(
        ForeignKey("checkpoints.id", ondelete="CASCADE"), nullable=True,
    )
    completion_criteria: Mapped[str] = mapped_column(
        String(16), nullable=False, default="scan", server_default="scan",
    )

    route: Mapped["Route"] = relationship("Route", back_populates="stops")

