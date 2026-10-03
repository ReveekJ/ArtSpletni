from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.admin import require_admin
from app.core.db import get_session
from app.entities.audio_track import AudioTrack
from app.entities.track_access_grant import TrackAccessGrant
from app.services.storage_service import get_storage
from app.services.track_service import TrackService

router = APIRouter(
    prefix="/api/admin/submissions",
    tags=["admin-submissions"],
    dependencies=[Depends(require_admin)],
)


class SubmissionRow(BaseModel):
    id: int
    title: str
    description: str | None
    author: str | None
    latitude: float
    longitude: float
    location_name: str | None
    moderation_status: str
    created_at: str
    audio_url: str


class SubmissionList(BaseModel):
    submissions: list[SubmissionRow]


class ModerationUpdate(BaseModel):
    moderation_status: Literal["pending", "published", "rejected"]


@router.get(
    "",
    response_model=SubmissionList,
    summary="List audio submissions for moderation",
)
async def list_submissions(session: AsyncSession = Depends(get_session)) -> SubmissionList:
    result = await session.execute(
        select(AudioTrack)
        .where(AudioTrack.moderation_status == "pending")
        .order_by(AudioTrack.created_at.desc())
    )
    storage = get_storage()
    return SubmissionList(
        submissions=[
            SubmissionRow(
                id=track.id,
                title=track.title,
                description=track.description,
                author=track.author,
                latitude=track.latitude or 0,
                longitude=track.longitude or 0,
                location_name=track.location_name,
                moderation_status=track.moderation_status,
                created_at=track.created_at.isoformat(),
                audio_url=storage.presign_get(track.audio_s3_key, 300),
            )
            for track in result.scalars().all()
        ]
    )


@router.patch(
    "/{track_id}",
    response_model=SubmissionRow,
    summary="Update an audio submission moderation status",
    responses={404: {"description": "Submission not found"}},
)
async def update_submission(
    track_id: int,
    payload: ModerationUpdate,
    session: AsyncSession = Depends(get_session),
) -> SubmissionRow:
    track = await session.get(AudioTrack, track_id)
    if track is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    track.moderation_status = payload.moderation_status
    track.is_published = payload.moderation_status == "published"
    if not track.is_published:
        await session.execute(
            update(TrackAccessGrant)
            .where(
                TrackAccessGrant.track_id == track.id,
                TrackAccessGrant.revoked_at.is_(None),
            )
            .values(revoked_at=TrackService.now_utc())
        )
    if track.is_published and track.published_at is None:
        track.published_at = TrackService.now_utc()
    await session.commit()
    await session.refresh(track)
    audio_url = (
        get_storage().presign_get(track.audio_s3_key, 300)
        if track.moderation_status != "rejected"
        else ""
    )
    return SubmissionRow(
        id=track.id,
        title=track.title,
        description=track.description,
        author=track.author,
        latitude=track.latitude or 0,
        longitude=track.longitude or 0,
        location_name=track.location_name,
        moderation_status=track.moderation_status,
        created_at=track.created_at.isoformat(),
        audio_url=audio_url,
    )