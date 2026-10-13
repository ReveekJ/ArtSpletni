from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base, TimestampMixin


class UserProgress(Base, TimestampMixin):
    __tablename__ = "user_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "route_stop_id", name="uq_user_progress_stop"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    route_stop_id: Mapped[int] = mapped_column(
        ForeignKey("route_stops.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
