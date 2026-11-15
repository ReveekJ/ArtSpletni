from uuid import UUID

from app.db.models import UserAchievement
from app.domain.achievements.services import UserAchievementRepository


class AchievementMerger:
    def __init__(self, earned: UserAchievementRepository) -> None:
        self._earned = earned

    async def merge_guest(self, guest_id: UUID, target_id: UUID) -> None:
        target_ids = {
            item.achievement_id for item in await self._earned.get_many(UserAchievement.user_id == target_id)
        }
        for item in await self._earned.get_many(UserAchievement.user_id == guest_id):
            if item.achievement_id in target_ids:
                await self._earned.delete(item.id)
                continue
            item.user_id = target_id
            await self._earned.update(item, auto_refresh=False)
