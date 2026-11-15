from litestar.di import NamedDependency
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.media.services import MediaRepository, MediaService
from app.domain.media.storage import object_storage


async def provide_media_service(db_session: NamedDependency[AsyncSession]) -> MediaService:
    return MediaService(MediaRepository(session=db_session), object_storage())
