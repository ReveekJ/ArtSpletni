from litestar.di import NamedDependency
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.i18n.services import TranslationService
from app.domain.media.services import MediaService
from app.domain.points.repositories import PointRepository
from app.domain.routes.admin_service import RouteAdminService
from app.domain.routes.repositories import RouteRepository


async def provide_route_admin_service(
    db_session: NamedDependency[AsyncSession],
    media_service: NamedDependency[MediaService],
    translation_service: NamedDependency[TranslationService],
) -> RouteAdminService:
    return RouteAdminService(
        RouteRepository(session=db_session),
        PointRepository(session=db_session),
        media_service,
        translation_service,
    )
