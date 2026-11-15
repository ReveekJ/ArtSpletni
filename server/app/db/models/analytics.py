from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class PlaybackEvent(UUIDv7AuditBase):
    __tablename__ = "playback_events"

    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None, index=True
    )
    point_id: Mapped[UUID] = mapped_column(ForeignKey("points.id", ondelete="CASCADE"), index=True)
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("media_assets.id", ondelete="CASCADE"), index=True)
    session_key: Mapped[str] = mapped_column(unique=True)
    position_seconds: Mapped[float]
    duration_seconds: Mapped[float]
    completed: Mapped[bool] = mapped_column(default=False)
