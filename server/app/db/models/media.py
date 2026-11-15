from enum import StrEnum
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.types import str_enum


class MediaKind(StrEnum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class MediaStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"


class MediaAsset(UUIDv7AuditBase):
    __tablename__ = "media_assets"

    storage_key: Mapped[str] = mapped_column(String(512), unique=True)
    kind: Mapped[MediaKind] = mapped_column(str_enum(MediaKind))
    content_type: Mapped[str] = mapped_column(String(128))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    original_filename: Mapped[str | None] = mapped_column(String(255), default=None)
    is_public: Mapped[bool] = mapped_column(default=False)
    status: Mapped[MediaStatus] = mapped_column(str_enum(MediaStatus), default=MediaStatus.PENDING)
    uploaded_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None, index=True
    )
