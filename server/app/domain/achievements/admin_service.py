from collections.abc import Sequence
from uuid import UUID

from app.db.models import Achievement, MediaKind
from app.domain.achievements.rules import dump_params, parse_params
from app.domain.achievements.schemas import AchievementInput
from app.domain.achievements.services import AchievementRepository
from app.domain.i18n.services import TranslationService
from app.domain.media.services import MediaService
from app.domain.offers.repositories import OfferRepository
from app.lib.exceptions import BadRequestError, ConflictError, NotFoundError


class AchievementAdminService:
    def __init__(
        self,
        achievements: AchievementRepository,
        offers: OfferRepository,
        media: MediaService,
        translator: TranslationService,
    ) -> None:
        self._achievements = achievements
        self._offers = offers
        self._media = media
        self._translator = translator

    async def list_all(self) -> Sequence[Achievement]:
        return await self._achievements.get_many(order_by=[(Achievement.position, False)])

    async def get(self, achievement_id: UUID) -> Achievement:
        achievement = await self._achievements.get_one_or_none(id=achievement_id)
        if achievement is None:
            raise NotFoundError("Achievement not found", code="achievement_not_found")
        return achievement

    async def create(self, data: AchievementInput) -> Achievement:
        achievement = Achievement(code=data.code, title={}, rule=data.rule, params={})
        await self._apply(achievement, data)
        return await self._achievements.add(achievement)

    async def update(self, achievement_id: UUID, data: AchievementInput) -> Achievement:
        achievement = await self.get(achievement_id)
        await self._apply(achievement, data)
        return await self._achievements.update(achievement, auto_refresh=False)

    async def delete(self, achievement_id: UUID) -> None:
        await self._achievements.delete((await self.get(achievement_id)).id)

    async def _apply(self, achievement: Achievement, data: AchievementInput) -> None:
        existing = await self._achievements.get_one_or_none(code=data.code)
        if existing is not None and existing.id != achievement.id:
            raise ConflictError("Code is already used", code="achievement_code_taken")
        title = await self._translator.localize(data.title, achievement.title or None)
        if title is None:
            raise BadRequestError("Title is required", code="title_required")
        if data.icon_asset_id is not None:
            await self._media.get_ready(data.icon_asset_id, MediaKind.IMAGE)
        if (
            data.reward_offer_id is not None
            and await self._offers.get_one_or_none(id=data.reward_offer_id) is None
        ):
            raise NotFoundError("Reward offer not found", code="offer_not_found")
        achievement.code = data.code
        achievement.title = title
        achievement.description = (
            await self._translator.localize(data.description, achievement.description, required=False)
            if data.description is not None
            else None
        )
        achievement.rule = data.rule
        achievement.params = dump_params(parse_params(data.rule, data.params))
        achievement.icon_asset_id = data.icon_asset_id
        achievement.is_hidden = data.is_hidden
        achievement.is_active = data.is_active
        achievement.position = data.position
        achievement.reward_offer_id = data.reward_offer_id
