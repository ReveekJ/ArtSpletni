from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base, TimestampMixin


class ListenSession(Base, TimestampMixin):
    __tablename__ = "listen_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    track_id: Mapped[int] = mapped_column(
        ForeignKey("audio_tracks.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    session_token: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    visitor_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)

    track_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    listened_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_position_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    completion_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    seek_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    referrer: Mapped[str | None] = mapped_column(String(512), nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
