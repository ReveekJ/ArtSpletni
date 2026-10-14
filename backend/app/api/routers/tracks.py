from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import get_current_user
from app.core.config import get_settings
from app.core.db import get_session
from app.entities.user import User
from app.repositories.route_stop_repo import RouteStopRepository
from app.services.progress_service import ProgressService
from app.services.storage_service import get_storage
from app.services.track_access_service import TrackAccessService
from app.services.track_service import DEFAULT_LANGUAGE, TrackService

router = APIRouter(prefix="/api/tracks", tags=["tracks"])
ACCESS_COOKIE_NAME = "spletni_track_access"


class TrackResponse(BaseModel):
    slug: str
    title: str
    description: str | None
    author: str | None
    audio_url: str
    cover_url: str | None
    latitude: float
    longitude: float
    location_name: str | None


def get_track_service(
    session: AsyncSession = Depends(get_session),
) -> TrackService:
    return TrackService(session, get_storage())


def get_access_service(
    session: AsyncSession = Depends(get_session),
) -> TrackAccessService:
    return TrackAccessService(session, get_settings().track_access_ttl_seconds)


@router.get(
    "/{slug}",
    response_model=TrackResponse,
    responses={
        404: {"description": "Track not found or not published"},
        401: {"description": "NFC access required or authentication required"},
        403: {"description": "Previous stops must be completed first"},
    },
    summary="Get a published audio track by its secret slug",
)
async def get_track(
    slug: str,
    lang: str | None = Query(default=None, description="Language code: ru, en, zh"),
    access_secret: str | None = Cookie(default=None, alias=ACCESS_COOKIE_NAME),
    service: TrackService = Depends(get_track_service),
    access_service: TrackAccessService = Depends(get_access_service),
    user: User | None = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TrackResponse:
    track = await service.get_track_entity_by_slug(slug)
    if track is None or track.moderation_status != "published":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )

    stop_repo = RouteStopRepository(session)
    route_stops = await stop_repo.find_route_stops_for_track(track.id)

    if route_stops and user is not None:
        progress_service = ProgressService(session)
        for stop in route_stops:
            if not await progress_service.is_stop_unlocked(stop, user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Previous stops must be completed first",
                )
    else:
        if not await access_service.is_granted(slug, access_secret):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="NFC access required",
            )

    resolved_language = TrackService.resolve_language(lang or DEFAULT_LANGUAGE)
    dto = await service.get_published_by_slug(
        slug,
        get_settings().track_access_ttl_seconds,
        resolved_language,
    )
    if dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )
    return TrackResponse(
        slug=dto.slug,
        title=dto.title,
        description=dto.description,
        author=dto.author,
        audio_url=dto.audio_url,
        cover_url=dto.cover_url,
        latitude=dto.latitude,
        longitude=dto.longitude,
        location_name=dto.location_name,
    )
