from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Achievement, AchievementRule, UserAchievement
from app.domain.achievements.rules import (
    COMPLETION_RULES,
    REDEMPTION_RULES,
    UNLOCK_RULES,
    AnyParams,
    CountParams,
    FirstFinishersParams,
    OptionalRouteParams,
    RouteParams,
    StreakParams,
    TimeWindowParams,
    WithinParams,
    parse_params,
)
from app.domain.achievements.stats import ProgressStats
from app.domain.offers.repositories import OfferRepository
from app.domain.offers.services import OfferService
from app.domain.runs.events import Notification, PointUnlocked, ProgressEvent, RouteCompleted
from app.lib.i18n import resolve_text


class AchievementRepository(SQLAlchemyAsyncRepository[Achievement]):
    model_type = Achievement


class UserAchievementRepository(SQLAlchemyAsyncRepository[UserAchievement]):
    model_type = UserAchievement

    async def award(self, user_id: UUID, achievement_id: UUID) -> bool:
        result = await self.session.execute(
            insert(UserAchievement)
            .values(user_id=user_id, achievement_id=achievement_id)
            .on_conflict_do_nothing(index_elements=[UserAchievement.user_id, UserAchievement.achievement_id])
            .returning(UserAchievement.id)
        )
        return result.scalar_one_or_none() is not None


@dataclass(frozen=True, slots=True)
class Progress:
    current: int
    target: int


@dataclass(frozen=True, slots=True)
class Redeemed:
    user_id: UUID
    at: datetime


AchievementTrigger = ProgressEvent | Redeemed


class AchievementService:
    def __init__(
        self,
        achievements: AchievementRepository,
        earned: UserAchievementRepository,
        stats: ProgressStats,
        offers: OfferService,
        offer_repository: OfferRepository,
        language: str,
        fallback: str,
    ) -> None:
        self._achievements = achievements
        self._earned = earned
        self._stats = stats
        self._offers = offers
        self._offer_repository = offer_repository
        self._language = language
        self._fallback = fallback

    async def handle(self, event: ProgressEvent) -> Sequence[Notification]:
        return await self.evaluate(event)

    async def evaluate(self, trigger: AchievementTrigger) -> list[Notification]:
        rules = self._rules_for(trigger)
        if not rules:
            return []
        user_id = trigger.user_id
        earned_ids = {
            item.achievement_id for item in await self._earned.get_many(UserAchievement.user_id == user_id)
        }
        candidates = await self._achievements.get_many(
            Achievement.rule.in_(rules), Achievement.is_active.is_(True)
        )
        notifications: list[Notification] = []
        for achievement in candidates:
            if achievement.id in earned_ids or not await self._is_met(achievement, trigger):
                continue
            if not await self._earned.award(user_id, achievement.id):
                continue
            notifications.append(
                Notification(
                    kind="achievement_earned",
                    id=achievement.id,
                    title=resolve_text(achievement.title, self._language, self._fallback),
                )
            )
            notifications.extend(await self._reward(user_id, achievement, trigger))
        return notifications

    async def earned(self, user_id: UUID) -> dict[UUID, datetime]:
        return {
            item.achievement_id: item.created_at
            for item in await self._earned.get_many(UserAchievement.user_id == user_id)
        }

    async def visible(self) -> Sequence[Achievement]:
        return await self._achievements.get_many(
            Achievement.is_active.is_(True), order_by=[(Achievement.position, False)]
        )

    async def progress(self, user_id: UUID, achievement: Achievement) -> Progress | None:
        params = parse_params(achievement.rule, achievement.params)
        match achievement.rule:
            case AchievementRule.POINTS_UNLOCKED if isinstance(params, CountParams):
                return Progress(await self._stats.unlocked_count(user_id), params.count)
            case AchievementRule.ROUTES_COMPLETED if isinstance(params, CountParams):
                return Progress(await self._stats.completed_routes_count(user_id), params.count)
            case AchievementRule.OFFERS_REDEEMED if isinstance(params, CountParams):
                return Progress(await self._stats.redeemed_count(user_id), params.count)
            case AchievementRule.PARTNER_POINTS_VISITED if isinstance(params, CountParams):
                return Progress(await self._stats.partner_points_count(user_id), params.count)
            case _:
                return None

    async def _is_met(self, achievement: Achievement, trigger: AchievementTrigger) -> bool:
        params = parse_params(achievement.rule, achievement.params)
        if isinstance(trigger, PointUnlocked):
            return await self._unlock_rule_met(achievement.rule, params, trigger)
        if isinstance(trigger, RouteCompleted):
            return await self._completion_rule_met(achievement.rule, params, trigger)
        if isinstance(trigger, Redeemed) and isinstance(params, CountParams):
            return await self._stats.redeemed_count(trigger.user_id) >= params.count
        return False

    async def _unlock_rule_met(
        self,
        rule: AchievementRule,
        params: AnyParams,
        event: PointUnlocked,
    ) -> bool:
        user_id = event.user_id
        if rule is AchievementRule.POINTS_UNLOCKED and isinstance(params, CountParams):
            return await self._stats.unlocked_count(user_id) >= params.count
        if rule is AchievementRule.PARTNER_POINTS_VISITED and isinstance(params, CountParams):
            return await self._stats.partner_points_count(user_id) >= params.count
        if rule is AchievementRule.POINTS_IN_DAY and isinstance(params, CountParams):
            return await self._stats.unlocks_on(user_id, self._stats.local_date(event.at)) >= params.count
        if rule is AchievementRule.DAYS_STREAK and isinstance(params, StreakParams):
            return await self._stats.streak_ending(user_id, self._stats.local_date(event.at)) >= params.days
        if rule is AchievementRule.SCAN_TIME_WINDOW and isinstance(params, TimeWindowParams):
            return _in_window(self._stats.local_hour(event.at), params.from_hour, params.to_hour)
        return False

    async def _completion_rule_met(
        self,
        rule: AchievementRule,
        params: AnyParams,
        event: RouteCompleted,
    ) -> bool:
        if rule is AchievementRule.ROUTE_COMPLETED and isinstance(params, RouteParams):
            return params.route_id == event.route_id
        if rule is AchievementRule.ROUTES_COMPLETED and isinstance(params, CountParams):
            return await self._stats.completed_routes_count(event.user_id) >= params.count
        if rule is AchievementRule.ROUTE_COMPLETED_FULL and isinstance(params, OptionalRouteParams):
            return event.fully and params.route_id in (None, event.route_id)
        if rule is AchievementRule.ROUTE_COMPLETED_WITHIN and isinstance(params, WithinParams):
            elapsed_hours = (event.at - event.started_at).total_seconds() / 3600
            return params.route_id in (None, event.route_id) and elapsed_hours <= params.hours
        if rule is AchievementRule.ROUTE_FIRST_FINISHERS and isinstance(params, FirstFinishersParams):
            if params.route_id not in (None, event.route_id):
                return False
            return await self._stats.finishers_count(event.route_id) <= params.count
        return False

    async def _reward(
        self, user_id: UUID, achievement: Achievement, trigger: AchievementTrigger
    ) -> list[Notification]:
        if achievement.reward_offer_id is None:
            return []
        offer = await self._offer_repository.get_one_or_none(id=achievement.reward_offer_id)
        if offer is None:
            return []
        grant = await self._offers.grant(user_id, offer, trigger.at)
        if grant is None:
            return []
        return [
            Notification(
                kind="offer_granted",
                id=grant.id,
                title=resolve_text(offer.title, self._language, self._fallback),
            )
        ]

    @staticmethod
    def _rules_for(trigger: AchievementTrigger) -> frozenset[AchievementRule]:
        if isinstance(trigger, PointUnlocked):
            return UNLOCK_RULES
        if isinstance(trigger, RouteCompleted):
            return COMPLETION_RULES
        if isinstance(trigger, Redeemed):
            return REDEMPTION_RULES
        return frozenset()


def _in_window(hour: int, start: int, end: int) -> bool:
    if start <= end:
        return start <= hour < end
    return hour >= start or hour < end
