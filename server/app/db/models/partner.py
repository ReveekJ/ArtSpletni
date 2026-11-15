from datetime import datetime
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.lib.i18n import LocalizedText, LocalizedTextType


class Partner(UUIDv7AuditBase):
    __tablename__ = "partners"

    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[LocalizedText | None] = mapped_column(LocalizedTextType(), default=None)
    logo_asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("media_assets.id", ondelete="SET NULL"), default=None
    )
    is_active: Mapped[bool] = mapped_column(default=True)


class PartnerMember(UUIDv7AuditBase):
    __tablename__ = "partner_members"
    __table_args__ = (UniqueConstraint("partner_id", "user_id"),)

    partner_id: Mapped[UUID] = mapped_column(ForeignKey("partners.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)


class Offer(UUIDv7AuditBase):
    __tablename__ = "offers"
    __table_args__ = (
        CheckConstraint("redemption_limit IS NULL OR redemption_limit > 0", name="positive_limit"),
        CheckConstraint("ttl_hours IS NULL OR ttl_hours > 0", name="positive_ttl"),
    )

    partner_id: Mapped[UUID] = mapped_column(ForeignKey("partners.id", ondelete="RESTRICT"), index=True)
    point_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("points.id", ondelete="CASCADE"), default=None, unique=True
    )
    title: Mapped[LocalizedText] = mapped_column(LocalizedTextType())
    terms: Mapped[LocalizedText | None] = mapped_column(LocalizedTextType(), default=None)
    promo_code: Mapped[str | None] = mapped_column(String(64), default=None)
    valid_until: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), default=None)
    ttl_hours: Mapped[int | None] = mapped_column(default=None)
    redemption_limit: Mapped[int | None] = mapped_column(default=None)
    redemptions_count: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

    @property
    def is_exhausted(self) -> bool:
        return self.redemption_limit is not None and self.redemptions_count >= self.redemption_limit


class OfferGrant(UUIDv7AuditBase):
    __tablename__ = "offer_grants"
    __table_args__ = (UniqueConstraint("offer_id", "user_id"),)

    offer_id: Mapped[UUID] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    redemption_code: Mapped[str] = mapped_column(String(16), unique=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), default=None)
    redeemed_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), default=None)
    redeemed_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
