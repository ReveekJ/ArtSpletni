from datetime import datetime
from enum import StrEnum
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.types import str_enum
from app.lib.i18n import LocalizedText, LocalizedTextType


class GossipStatus(StrEnum):
    NONE = "none"
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class GossipCategory(StrEnum):
    FUN = "fun"
    MYSTIC = "mystic"
    ROMANCE = "romance"
    LEGEND = "legend"
    HISTORY = "history"


class GossipVeracity(StrEnum):
    LEGEND = "legend"
    UNVERIFIED = "unverified"
    DOCUMENTED = "documented"


class GossipSourceOrigin(StrEnum):
    WIKIPEDIA = "wikipedia"
    LLM_WEB = "llm_web"


class GossipGeneration(UUIDv7AuditBase):
    __tablename__ = "gossip_generations"

    point_id: Mapped[UUID] = mapped_column(ForeignKey("points.id", ondelete="CASCADE"), unique=True)
    status: Mapped[GossipStatus] = mapped_column(str_enum(GossipStatus), default=GossipStatus.PENDING)
    attempt_id: Mapped[UUID]
    latitude: Mapped[float]
    longitude: Mapped[float]
    error: Mapped[str | None] = mapped_column(Text, default=None)
    finished_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), default=None)


class GossipSource(UUIDv7AuditBase):
    __tablename__ = "gossip_sources"

    item_id: Mapped[UUID] = mapped_column(ForeignKey("gossip_items.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(2048))
    title: Mapped[str | None] = mapped_column(String(512), default=None)
    origin: Mapped[GossipSourceOrigin] = mapped_column(str_enum(GossipSourceOrigin))


class GossipItem(UUIDv7AuditBase):
    __tablename__ = "gossip_items"

    point_id: Mapped[UUID] = mapped_column(ForeignKey("points.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]
    category: Mapped[GossipCategory] = mapped_column(str_enum(GossipCategory))
    veracity: Mapped[GossipVeracity] = mapped_column(str_enum(GossipVeracity))
    title: Mapped[LocalizedText] = mapped_column(LocalizedTextType())
    text: Mapped[LocalizedText] = mapped_column(LocalizedTextType())
    place_name: Mapped[str | None] = mapped_column(String(255), default=None)
    latitude: Mapped[float | None] = mapped_column(default=None)
    longitude: Mapped[float | None] = mapped_column(default=None)
    distance_m: Mapped[int | None] = mapped_column(default=None)
    photo_url: Mapped[str | None] = mapped_column(String(2048), default=None)
    photo_author: Mapped[str | None] = mapped_column(String(512), default=None)
    photo_license: Mapped[str | None] = mapped_column(String(128), default=None)
    photo_source_url: Mapped[str | None] = mapped_column(String(2048), default=None)
    is_hidden: Mapped[bool] = mapped_column(default=False)
    sources: Mapped[list[GossipSource]] = relationship(
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="GossipSource.created_at",
    )
