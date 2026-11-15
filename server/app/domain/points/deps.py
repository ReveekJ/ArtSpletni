from litestar.di import NamedDependency
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.i18n.services import TranslationService
from app.domain.media.services import MediaService
from app.domain.partners.services import PartnerRepository
from app.domain.points.admin_service import PointAdminService
from app.domain.points.content_service import PointContentService
from app.domain.points.repositories import PointRepository, UnlockRepository
from app.lib.settings import get_settings


async def provide_point_admin_service(
    db_session: NamedDependency[AsyncSession],
    media_service: NamedDependency[MediaService],
    translation_service: NamedDependency[TranslationService],
) -> PointAdminService:
    return PointAdminService(
        PointRepository(session=db_session),
        PartnerRepository(session=db_session),
        media_service,
        translation_service,
    )


async def provide_point_content_service(
    db_session: NamedDependency[AsyncSession],
    media_service: NamedDependency[MediaService],
    language: NamedDependency[str],
) -> PointContentService:
    return PointContentService(
        PointRepository(session=db_session),
        UnlockRepository(session=db_session),
        media_service,
        language,
        get_settings().default_language,
    )
