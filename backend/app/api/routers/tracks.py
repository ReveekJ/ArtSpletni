from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.services.storage_service import get_storage
from app.services.track_service import TrackService

router = APIRouter(prefix="/api/tracks", tags=["tracks"])


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


@router.get(
    "/{slug}",
    response_model=TrackResponse,
    responses={404: {"description": "Track not found or not published"}},
    summary="Get a published audio track by its secret slug",
)
async def get_track(slug: str, service: TrackService = Depends(get_track_service)) -> TrackResponse:
    dto = await service.get_published_by_slug(slug)
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
