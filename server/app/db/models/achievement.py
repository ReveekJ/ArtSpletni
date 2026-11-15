from enum import StrEnum
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.types import str_enum
from app.lib.i18n import LocalizedText, LocalizedTextType

RuleParams = dict[str, int | str | None]


class AchievementRule(StrEnum):
    POINTS_UNLOCKED = "points_unlocked"
    ROUTE_COMPLETED = "route_completed"
    ROUTES_COMPLETED = "routes_completed"
    ROUTE_COMPLETED_FULL = "route_completed_full"
    ROUTE_COMPLETED_WITHIN = "route_completed_within"
    ROUTE_FIRST_FINISHERS = "route_first_finishers"
    OFFERS_REDEEMED = "offers_redeemed"
    PARTNER_POINTS_VISITED = "partner_points_visited"
    SCAN_TIME_WINDOW = "scan_time_window"
    POINTS_IN_DAY = "points_in_day"
    DAYS_STREAK = "days_streak"


class Achievement(UUIDv7AuditBase):
    __tablename__ = "achievements"

    code: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[LocalizedText] = mapped_column(LocalizedTextType())
    description: Mapped[LocalizedText | None] = mapped_column(LocalizedTextType(), default=None)
    icon_asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("media_assets.id", ondelete="SET NULL"), default=None
    )
    rule: Mapped[AchievementRule] = mapped_column(str_enum(AchievementRule), index=True)
    params: Mapped[RuleParams] = mapped_column(JSONB, default=dict)
    is_hidden: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    position: Mapped[int] = mapped_column(default=0)
    reward_offer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("offers.id", ondelete="SET NULL"), default=None
    )


class UserAchievement(UUIDv7AuditBase):
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    achievement_id: Mapped[UUID] = mapped_column(
        ForeignKey("achievements.id", ondelete="CASCADE"), index=True
    )
