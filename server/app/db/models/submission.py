from enum import StrEnum
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.types import str_enum


class SubmissionStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class SubmissionMedia(UUIDv7AuditBase):
    __tablename__ = "submission_media"
    __table_args__ = (UniqueConstraint("submission_id", "asset_id"),)

    submission_id: Mapped[UUID] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), index=True)
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("media_assets.id", ondelete="CASCADE"))
    position: Mapped[int]


class Submission(UUIDv7AuditBase):
    __tablename__ = "submissions"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    story: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(8))
    latitude: Mapped[float]
    longitude: Mapped[float]
    status: Mapped[SubmissionStatus] = mapped_column(
        str_enum(SubmissionStatus), default=SubmissionStatus.PENDING, index=True
    )
    moderator_comment: Mapped[str | None] = mapped_column(Text, default=None)
    point_id: Mapped[UUID | None] = mapped_column(ForeignKey("points.id", ondelete="SET NULL"), default=None)
    media: Mapped[list[SubmissionMedia]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="SubmissionMedia.position"
    )
