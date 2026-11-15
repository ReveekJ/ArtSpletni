from uuid import UUID

from litestar import Controller, delete, get, post, put
from litestar.di import NamedDependency, Provide
from litestar.params import FromPath, JSONBody

from app.domain.achievements.admin_service import AchievementAdminService
from app.domain.achievements.deps import provide_achievement_admin_service, provide_achievement_service
from app.domain.achievements.schemas import (
    AchievementInput,
    AdminAchievementOut,
    MyAchievementOut,
    ProgressOut,
)
from app.domain.achievements.services import AchievementService
from app.domain.auth.guards import requires_actor, requires_admin
from app.domain.media.services import MediaService
from app.lib.i18n import resolve_text
from app.lib.request import AppRequest, require_user
from app.lib.settings import get_settings


class AdminAchievementController(Controller):
    path = "/api/admin/achievements"
    tags = ["Admin: Achievements"]
    guards = [requires_admin]
    dependencies = {"achievement_admin_service": Provide(provide_achievement_admin_service)}

    @get("/", summary="List achievements", description="All achievements including inactive ones.")
    async def list_achievements(
        self, achievement_admin_service: NamedDependency[AchievementAdminService]
    ) -> list[AdminAchievementOut]:
        return [AdminAchievementOut.from_model(item) for item in await achievement_admin_service.list_all()]

    @post(
        "/",
        summary="Create achievement",
        description="Create an achievement from a rule type and parameters.",
    )
    async def create_achievement(
        self,
        data: JSONBody[AchievementInput],
        achievement_admin_service: NamedDependency[AchievementAdminService],
    ) -> AdminAchievementOut:
        return AdminAchievementOut.from_model(await achievement_admin_service.create(data))

    @put("/{achievement_id:uuid}", summary="Update achievement", description="Update achievement settings.")
    async def update_achievement(
        self,
        achievement_id: FromPath[UUID],
        data: JSONBody[AchievementInput],
        achievement_admin_service: NamedDependency[AchievementAdminService],
    ) -> AdminAchievementOut:
        return AdminAchievementOut.from_model(await achievement_admin_service.update(achievement_id, data))

    @delete("/{achievement_id:uuid}", summary="Delete achievement", description="Delete an achievement.")
    async def delete_achievement(
        self,
        achievement_id: FromPath[UUID],
        achievement_admin_service: NamedDependency[AchievementAdminService],
    ) -> None:
        await achievement_admin_service.delete(achievement_id)


class MyAchievementsController(Controller):
    path = "/api/me/achievements"
    tags = ["Me"]
    guards = [requires_actor]
    dependencies = {"achievement_service": Provide(provide_achievement_service)}

    @get(
        "/",
        summary="My achievements",
        description="Visible achievements with earned dates and progress; hidden ones appear once earned.",
    )
    async def my_achievements(
        self,
        request: AppRequest,
        language: NamedDependency[str],
        achievement_service: NamedDependency[AchievementService],
        media_service: NamedDependency[MediaService],
    ) -> list[MyAchievementOut]:
        user = require_user(request)
        fallback = get_settings().default_language
        earned = await achievement_service.earned(user.id)
        achievements = [
            item for item in await achievement_service.visible() if not item.is_hidden or item.id in earned
        ]
        icons = await media_service.get_many(
            {item.icon_asset_id for item in achievements if item.icon_asset_id}
        )
        result: list[MyAchievementOut] = []
        for item in achievements:
            progress = None if item.id in earned else await achievement_service.progress(user.id, item)
            icon = icons.get(item.icon_asset_id) if item.icon_asset_id else None
            result.append(
                MyAchievementOut(
                    id=item.id,
                    code=item.code,
                    title=resolve_text(item.title, language, fallback) or item.code,
                    description=resolve_text(item.description, language, fallback),
                    icon_url=await media_service.download_url(icon) if icon else None,
                    is_hidden=item.is_hidden,
                    earned_at=earned.get(item.id),
                    progress=ProgressOut(
                        current=min(progress.current, progress.target), target=progress.target
                    )
                    if progress
                    else None,
                    has_reward=item.reward_offer_id is not None,
                )
            )
        return result
