import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_session
from app.entities.audio_track import AudioTrack
from app.repositories.audio_track_repo import AudioTrackRepository
from app.services.storage_service import get_storage
from app.services.track_service import TrackService

router = APIRouter(prefix="/api/submissions", tags=["submissions"])
REQUIRED_FILE = File(...)
ALLOWED_AUDIO_TYPES = {
    ".aac": {"audio/aac", "audio/x-aac", "application/octet-stream"},
    ".m4a": {"audio/mp4", "audio/x-m4a", "application/octet-stream"},
    ".mp3": {"audio/mpeg", "audio/mp3", "application/octet-stream"},
    ".ogg": {"audio/ogg", "application/ogg", "application/octet-stream"},
    ".wav": {"audio/wav", "audio/x-wav", "audio/wave", "application/octet-stream"},
}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Submit an audio story for moderation",
    responses={
        201: {"description": "Submission received for review"},
        413: {"description": "Audio file exceeds 10 MiB"},
    },
)
async def submit_audio_story(
    audio_file: UploadFile = REQUIRED_FILE,
    title: str = Form(min_length=1, max_length=255),
    latitude: float = Form(ge=-90, le=90),
    longitude: float = Form(ge=-180, le=180),
    location_name: str | None = Form(default=None, max_length=255),
    description: str | None = Form(default=None),
    author: str | None = Form(default=None, max_length=255),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    settings = get_settings()
    extension = Path(audio_file.filename or "").suffix.lower()
    if extension not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported audio format",
        )
    if audio_file.content_type not in ALLOWED_AUDIO_TYPES[extension]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Audio content type does not match the file format",
        )

    content = await audio_file.read(settings.submission_max_audio_bytes + 1)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Audio file is empty",
        )
    if len(content) > settings.submission_max_audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio file exceeds 10 MiB",
        )

    slug = TrackService.generate_slug()
    key = f"submissions/{secrets.token_urlsafe(16)}{extension}"
    storage = get_storage()
    storage.upload(key, content, audio_file.content_type or "application/octet-stream")
    track = AudioTrack(
        slug=slug,
        title=title.strip(),
        description=description,
        author=author,
        audio_s3_key=key,
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        is_published=False,
        moderation_status="pending",
    )
    try:
        await AudioTrackRepository(session).create(track)
    except Exception:
        storage.delete(key)
        raise
    return {"message": "Предложение отправлено на проверку"}