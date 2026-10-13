from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.admin import require_admin
from app.core.db import get_session
from app.entities.track_localization import TrackLocalization
from app.repositories.audio_track_repo import AudioTrackRepository
from app.repositories.track_localization_repo import TrackLocalizationRepository
from app.services.storage_service import get_storage

router = APIRouter(
    prefix="/api/admin/tracks/{track_id}/localizations",
    tags=["admin-track-localizations"],
    dependencies=[Depends(require_admin)],
)

ALLOWED_LANGUAGES: tuple[str, ...] = ("ru", "en", "zh")


class LocalizationCreatePayload(BaseModel):
    language: Literal["ru", "en", "zh"]
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    location_name: str | None = Field(default=None, max_length=255)


class LocalizationUpdatePayload(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    location_name: str | None = Field(default=None, max_length=255)


class LocalizationResponse(BaseModel):
    id: int
    track_id: int
    language: str
    title: str
    description: str | None
    location_name: str | None
    has_audio: bool
    has_cover: bool


class LocalizationListResponse(BaseModel):
    localizations: list[LocalizationResponse]


def _to_response(loc: TrackLocalization) -> LocalizationResponse:
    return LocalizationResponse(
        id=loc.id,
        track_id=loc.track_id,
        language=loc.language,
        title=loc.title,
        description=loc.description,
        location_name=loc.location_name,
        has_audio=loc.audio_s3_key is not None,
        has_cover=loc.cover_s3_key is not None,
    )


async def _get_track_or_404(track_id: int, session: AsyncSession) -> None:
    track = await AudioTrackRepository(session).get_by_id(track_id)
    if track is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )


@router.get(
    "",
    response_model=LocalizationListResponse,
    summary="List all localizations for a track (admin)",
)
async def list_localizations(
    track_id: int,
    session: AsyncSession = Depends(get_session),
) -> LocalizationListResponse:
    await _get_track_or_404(track_id, session)
    repo = TrackLocalizationRepository(session)
    locs = await repo.list_for_track(track_id)
    return LocalizationListResponse(
        localizations=[_to_response(loc) for loc in locs],
    )


@router.post(
    "",
    response_model=LocalizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a localization for a track (admin)",
    responses={
        404: {"description": "Track not found"},
        409: {"description": "Localization for this language already exists"},
    },
)
async def create_localization(
    track_id: int,
    payload: LocalizationCreatePayload,
    session: AsyncSession = Depends(get_session),
) -> LocalizationResponse:
    await _get_track_or_404(track_id, session)
    repo = TrackLocalizationRepository(session)
    existing = await repo.get_by_track_and_language(track_id, payload.language)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Localization for this language already exists",
        )
    loc = TrackLocalization(
        track_id=track_id,
        language=payload.language,
        title=payload.title,
        description=payload.description,
        location_name=payload.location_name,
    )
    loc = await repo.create(loc)
    return _to_response(loc)


@router.patch(
    "/{language}",
    response_model=LocalizationResponse,
    summary="Update a localization for a track (admin)",
    responses={404: {"description": "Track or localization not found"}},
)
async def update_localization(
    track_id: int,
    language: Literal["ru", "en", "zh"],
    payload: LocalizationUpdatePayload,
    session: AsyncSession = Depends(get_session),
) -> LocalizationResponse:
    await _get_track_or_404(track_id, session)
    repo = TrackLocalizationRepository(session)
    loc = await repo.get_by_track_and_language(track_id, language)
    if loc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Localization not found",
        )
    if payload.title is not None:
        loc.title = payload.title
    if payload.description is not None:
        loc.description = payload.description
    if payload.location_name is not None:
        loc.location_name = payload.location_name
    loc = await repo.update(loc)
    return _to_response(loc)


@router.delete(
    "/{language}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a localization for a track (admin)",
    responses={404: {"description": "Track or localization not found"}},
)
async def delete_localization(
    track_id: int,
    language: Literal["ru", "en", "zh"],
    session: AsyncSession = Depends(get_session),
) -> None:
    await _get_track_or_404(track_id, session)
    repo = TrackLocalizationRepository(session)
    loc = await repo.get_by_track_and_language(track_id, language)
    if loc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Localization not found",
        )
    storage = get_storage()
    if loc.audio_s3_key:
        storage.delete(loc.audio_s3_key)
    if loc.cover_s3_key:
        storage.delete(loc.cover_s3_key)
    await repo.delete(loc)
