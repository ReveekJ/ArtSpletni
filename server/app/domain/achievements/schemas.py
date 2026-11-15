from datetime import datetime
from typing import Annotated
from uuid import UUID

import msgspec

from app.db.models import Achievement, AchievementRule, RuleParams
from app.domain.i18n.schemas import LocalizedField, LocalizedInput, localized_out
from app.lib.schema import CamelizedBaseStruct


class AchievementInput(CamelizedBaseStruct):
    code: Annotated[str, msgspec.Meta(pattern=r"^[a-z0-9_]+$", max_length=64)]
    title: LocalizedInput
    rule: AchievementRule
    params: RuleParams
    description: LocalizedInput | None = None
    icon_asset_id: UUID | None = None
    is_hidden: bool = False
    is_active: bool = True
    position: int = 0
    reward_offer_id: UUID | None = None


class AdminAchievementOut(CamelizedBaseStruct):
    id: UUID
    code: str
    title: dict[str, LocalizedField]
    description: dict[str, LocalizedField]
    icon_asset_id: UUID | None
    rule: AchievementRule
    params: RuleParams
    is_hidden: bool
    is_active: bool
    position: int
    reward_offer_id: UUID | None

    @classmethod
    def from_model(cls, achievement: Achievement) -> "AdminAchievementOut":
        return cls(
            id=achievement.id,
            code=achievement.code,
            title=localized_out(achievement.title),
            description=localized_out(achievement.description),
            icon_asset_id=achievement.icon_asset_id,
            rule=achievement.rule,
            params=achievement.params,
            is_hidden=achievement.is_hidden,
            is_active=achievement.is_active,
            position=achievement.position,
            reward_offer_id=achievement.reward_offer_id,
        )


class ProgressOut(CamelizedBaseStruct):
    current: int
    target: int


class MyAchievementOut(CamelizedBaseStruct):
    id: UUID
    code: str
    title: str
    description: str | None
    icon_url: str | None
    is_hidden: bool
    earned_at: datetime | None
    progress: ProgressOut | None
    has_reward: bool
