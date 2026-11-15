from datetime import datetime
from enum import StrEnum
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.types import str_enum
from app.lib.i18n import LocalizedText, LocalizedTextType


class PointKind(StrEnum):
    GOSSIP = "gossip"
    PARTNER = "partner"


class BlockKind(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class ContentBlockMedia(UUIDv7AuditBase):
    __tablename__ = "content_block_media"
    __table_args__ = (UniqueConstraint("block_id", "language"),)

    block_id: Mapped[UUID] = mapped_column(ForeignKey("content_blocks.id", ondelete="CASCADE"), index=True)
    language: Mapped[str] = mapped_column(String(8))
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("media_assets.id", ondelete="RESTRICT"))


class ContentBlock(UUIDv7AuditBase):
    __tablename__ = "content_blocks"

    point_id: Mapped[UUID] = mapped_column(ForeignKey("points.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]
    kind: Mapped[BlockKind] = mapped_column(str_enum(BlockKind))
    text: Mapped[LocalizedText | None] = mapped_column(LocalizedTextType(), default=None)
    caption: Mapped[LocalizedText | None] = mapped_column(LocalizedTextType(), default=None)
    asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("media_assets.id", ondelete="RESTRICT"), default=None
    )
    media_variants: Mapped[list[ContentBlockMedia]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


class Point(UUIDv7AuditBase):
    __tablename__ = "points"

    kind: Mapped[PointKind] = mapped_column(str_enum(PointKind))
    title: Mapped[LocalizedText] = mapped_column(LocalizedTextType())
    latitude: Mapped[float]
    longitude: Mapped[float]
    address: Mapped[LocalizedText | None] = mapped_column(LocalizedTextType(), default=None)
    note: Mapped[LocalizedText | None] = mapped_column(LocalizedTextType(), default=None)
    cover_asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("media_assets.id", ondelete="SET NULL"), default=None
    )
    partner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("partners.id", ondelete="RESTRICT"), default=None, index=True
    )
    is_published: Mapped[bool] = mapped_column(default=False)
    blocks: Mapped[list[ContentBlock]] = relationship(
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ContentBlock.position",
    )


class NfcTag(UUIDv7AuditBase):
    __tablename__ = "nfc_tags"

    point_id: Mapped[UUID] = mapped_column(ForeignKey("points.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    label: Mapped[str | None] = mapped_column(String(120), default=None)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), default=None)
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), default=None)


class Unlock(UUIDv7AuditBase):
    __tablename__ = "unlocks"
    __table_args__ = (UniqueConstraint("user_id", "point_id"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    point_id: Mapped[UUID] = mapped_column(ForeignKey("points.id", ondelete="CASCADE"), index=True)
