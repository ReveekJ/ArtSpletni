from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base, TimestampMixin


class TrackLocalization(Base, TimestampMixin):
    __tablename__ = "track_localizations"
    __table_args__ = (
        UniqueConstraint("track_id", "language", name="uq_track_localizations_track_language"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    track_id: Mapped[int] = mapped_column(
        ForeignKey("audio_tracks.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    language: Mapped[str] = mapped_column(String(2), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audio_s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    cover_s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
