from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base, TimestampMixin


class RouteStopDependency(Base, TimestampMixin):
    __tablename__ = "route_stop_dependencies"
    __table_args__ = (
        UniqueConstraint(
            "route_stop_id", "depends_on_stop_id",
            name="uq_route_stop_dependency_pair",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    route_stop_id: Mapped[int] = mapped_column(
        ForeignKey("route_stops.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    depends_on_stop_id: Mapped[int] = mapped_column(
        ForeignKey("route_stops.id", ondelete="CASCADE"), nullable=False, index=True,
    )
