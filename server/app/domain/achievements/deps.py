from litestar.di import NamedDependency
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.achievements.admin_service import AchievementAdminService
from app.domain.achievements.services import (
    AchievementRepository,
    AchievementService,
    UserAchievementRepository,
)
from app.domain.achievements.stats import ProgressStats
from app.domain.i18n.services import TranslationService
from app.domain.media.services import MediaService
from app.domain.offers.deps import build_offer_service
from app.domain.offers.repositories import OfferRepository
from app.lib.settings import get_settings


def build_achievement_service(db_session: AsyncSession, language: str) -> AchievementService:
    settings = get_settings()
    return AchievementService(
        AchievementRepository(session=db_session),
        UserAchievementRepository(session=db_session),
        ProgressStats(db_session, settings.timezone),
        build_offer_service(db_session),
        OfferRepository(session=db_session),
        language,
        settings.default_language,
    )


async def provide_achievement_service(
    db_session: NamedDependency[AsyncSession], language: NamedDependency[str]
) -> AchievementService:
    return build_achievement_service(db_session, language)


def build_achievement_admin_service(
    db_session: AsyncSession, media: MediaService, translator: TranslationService
) -> AchievementAdminService:
    return AchievementAdminService(
        AchievementRepository(session=db_session),
        OfferRepository(session=db_session),
        media,
        translator,
    )


async def provide_achievement_admin_service(
    db_session: NamedDependency[AsyncSession],
    media_service: NamedDependency[MediaService],
    translation_service: NamedDependency[TranslationService],
) -> AchievementAdminService:
    return build_achievement_admin_service(db_session, media_service, translation_service)
