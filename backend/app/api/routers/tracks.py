from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_session
from app.services.storage_service import get_storage
from app.services.track_access_service import TrackAccessService
from app.services.track_service import TrackService

router = APIRouter(prefix="/api/tracks", tags=["tracks"])
ACCESS_COOKIE_NAME = "spletni_track_access"


class TrackResponse(BaseModel):
    slug: str
    title: str
    description: str | None
    author: str | None
    audio_url: str
    cover_url: str | None
    latitude: float | None
    longitude: float | None
    location_name: str | None


def get_track_service(
    session: AsyncSession = Depends(get_session),
) -> TrackService:
    return TrackService(session, get_storage())


def get_access_service(
    session: AsyncSession = Depends(get_session),
) -> TrackAccessService:
    return TrackAccessService(session, get_settings().track_access_ttl_seconds)


@router.get("/nfc/{slug}", include_in_schema=False)
async def bootstrap_track_access(
    slug: str,
    response: Response,
    service: TrackService = Depends(get_track_service),
    access_service: TrackAccessService = Depends(get_access_service),
) -> Response:
    track = await service.get_track_entity_by_slug(slug)
    if track is None or track.moderation_status != "published":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not found")

    secret = await access_service.create_grant(track)
    response.set_cookie(
        ACCESS_COOKIE_NAME,
        secret,
        max_age=get_settings().track_access_ttl_seconds,
        httponly=True,
        secure=get_settings().track_access_cookie_secure,
        samesite="lax",
        path="/",
    )
    response.status_code = status.HTTP_302_FOUND
    response.headers["Location"] = f"/t/{track.slug}"
    return response


@router.get(
    "/{slug}",
    response_model=TrackResponse,
    responses={404: {"description": "Track not found or not published"}},
    summary="Get a published audio track by its secret slug",
)
async def get_track(
    slug: str,
    access_secret: str | None = Cookie(default=None, alias=ACCESS_COOKIE_NAME),
    service: TrackService = Depends(get_track_service),
    access_service: TrackAccessService = Depends(get_access_service),
) -> TrackResponse:
    if not await access_service.is_granted(slug, access_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="NFC access required",
        )
    dto = await service.get_published_by_slug(
        slug,
        get_settings().track_access_ttl_seconds,
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
