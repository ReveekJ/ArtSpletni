import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.admin import require_admin
from app.core.config import get_settings
from app.core.db import get_session
from app.entities.audio_track import AudioTrack
from app.repositories.audio_track_repo import AudioTrackRepository
from app.services.storage_service import get_storage
from app.services.track_service import TrackService

router = APIRouter(
    prefix="/api/admin/tracks",
    tags=["admin-tracks"],
    dependencies=[Depends(require_admin)],
)

REQUIRED_AUDIO = File(...)
OPTIONAL_AUDIO = File(default=None)
OPTIONAL_COVER = File(default=None)

ALLOWED_AUDIO_TYPES = {
    ".aac": {"audio/aac", "audio/x-aac", "application/octet-stream"},
    ".m4a": {"audio/mp4", "audio/x-m4a", "application/octet-stream"},
    ".mp3": {"audio/mpeg", "audio/mp3", "application/octet-stream"},
    ".ogg": {"audio/ogg", "application/ogg", "application/octet-stream"},
    ".wav": {"audio/wav", "audio/x-wav", "audio/wave", "application/octet-stream"},
}

ALLOWED_IMAGE_TYPES = {
    ".jpg": {"image/jpeg", "application/octet-stream"},
    ".jpeg": {"image/jpeg", "application/octet-stream"},
    ".png": {"image/png", "application/octet-stream"},
    ".webp": {"image/webp", "application/octet-stream"},
}


class TrackAdminItem(BaseModel):
    id: int
    slug: str
    title: str
    description: str | None
    author: str | None
    latitude: float
    longitude: float
    location_name: str | None
    is_published: bool
    moderation_status: str


class TrackAdminList(BaseModel):
    tracks: list[TrackAdminItem]


class TrackAdminDetail(BaseModel):
    id: int
    slug: str
    title: str
    description: str | None
    author: str | None
    latitude: float
    longitude: float
    location_name: str | None
    is_published: bool
    moderation_status: str
    audio_url: str
    cover_url: str | None
    created_at: str
    published_at: str | None


async def _read_and_validate_audio(
    audio_file: UploadFile,
) -> tuple[str, bytes, str]:
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
            detail="Audio file exceeds size limit",
        )
    return extension, content, audio_file.content_type or "application/octet-stream"


async def _read_and_validate_cover(
    cover_file: UploadFile,
) -> tuple[str, bytes, str]:
    settings = get_settings()
    extension = Path(cover_file.filename or "").suffix.lower()
    if extension not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported image format",
        )
    if cover_file.content_type not in ALLOWED_IMAGE_TYPES[extension]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Image content type does not match the file format",
        )
    content = await cover_file.read(settings.submission_max_image_bytes + 1)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cover image is empty",
        )
    if len(content) > settings.submission_max_image_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Cover image exceeds size limit",
        )
    return extension, content, cover_file.content_type or "image/jpeg"


def _to_detail(track: AudioTrack, audio_url: str, cover_url: str | None) -> TrackAdminDetail:
    return TrackAdminDetail(
        id=track.id,
        slug=track.slug,
        title=track.title,
        description=track.description,
        author=track.author,
        latitude=track.latitude,
        longitude=track.longitude,
        location_name=track.location_name,
        is_published=track.is_published,
        moderation_status=track.moderation_status,
        audio_url=audio_url,
        cover_url=cover_url,
        created_at=track.created_at.isoformat(),
        published_at=track.published_at.isoformat() if track.published_at else None,
    )


def _presign_urls(
    track: AudioTrack,
    ttl_seconds: int = 300,
) -> tuple[str, str | None]:
    storage = get_storage()
    audio_url = storage.presign_get(track.audio_s3_key, ttl_seconds)
    cover_url = (
        storage.presign_get(track.cover_s3_key, ttl_seconds)
        if track.cover_s3_key
        else None
    )
    return audio_url, cover_url


@router.get(
    "",
    response_model=TrackAdminList,
    summary="List all tracks (admin)",
)
async def list_tracks(
    session: AsyncSession = Depends(get_session),
) -> TrackAdminList:
    repo = AudioTrackRepository(session)
    tracks = await repo.list_all()
    return TrackAdminList(
        tracks=[
            TrackAdminItem(
                id=t.id,
                slug=t.slug,
                title=t.title,
                description=t.description,
                author=t.author,
                latitude=t.latitude,
                longitude=t.longitude,
                location_name=t.location_name,
                is_published=t.is_published,
                moderation_status=t.moderation_status,
            )
            for t in tracks
        ],
    )


@router.get(
    "/{track_id}",
    response_model=TrackAdminDetail,
    summary="Get a single track detail (admin)",
    responses={404: {"description": "Track not found"}},
)
async def get_track(
    track_id: int,
    session: AsyncSession = Depends(get_session),
) -> TrackAdminDetail:
    repo = AudioTrackRepository(session)
    track = await repo.get_by_id(track_id)
    if track is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )
    audio_url, cover_url = _presign_urls(track)
    return _to_detail(track, audio_url, cover_url)


@router.post(
    "",
    response_model=TrackAdminDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new track (admin, auto-published)",
    responses={
        415: {"description": "Unsupported media type"},
        413: {"description": "File exceeds size limit"},
        422: {"description": "File is empty"},
    },
)
async def create_track(
    audio_file: UploadFile = REQUIRED_AUDIO,
    cover_file: UploadFile | None = OPTIONAL_COVER,
    title: str = Form(min_length=1, max_length=255),
    description: str | None = Form(default=None),
    author: str | None = Form(default=None, max_length=255),
    latitude: float = Form(ge=-90, le=90),
    longitude: float = Form(ge=-180, le=180),
    location_name: str | None = Form(default=None, max_length=255),
    session: AsyncSession = Depends(get_session),
) -> TrackAdminDetail:
    audio_ext, audio_content, audio_ct = await _read_and_validate_audio(audio_file)

    cover_ext: str | None = None
    cover_content: bytes | None = None
    cover_ct: str | None = None
    if cover_file is not None and cover_file.filename:
        cover_ext, cover_content, cover_ct = await _read_and_validate_cover(cover_file)

    storage = get_storage()
    audio_key = f"tracks/{secrets.token_urlsafe(16)}{audio_ext}"
    storage.upload(audio_key, audio_content, audio_ct)

    cover_key: str | None = None
    if cover_content is not None:
        cover_key = f"covers/{secrets.token_urlsafe(16)}{cover_ext}"
        storage.upload(cover_key, cover_content, cover_ct)

    track = AudioTrack(
        slug=TrackService.generate_slug(),
        title=title.strip(),
        description=description,
        author=author,
        audio_s3_key=audio_key,
        cover_s3_key=cover_key,
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        is_published=True,
        moderation_status="published",
        published_at=TrackService.now_utc(),
    )
    try:
        track = await AudioTrackRepository(session).create(track)
    except Exception:
        storage.delete(audio_key)
        if cover_key:
            storage.delete(cover_key)
        raise

    audio_url, cover_url = _presign_urls(track)
    return _to_detail(track, audio_url, cover_url)


@router.patch(
    "/{track_id}",
    response_model=TrackAdminDetail,
    summary="Update a track (admin) — metadata and/or file replacement",
    responses={
        404: {"description": "Track not found"},
        415: {"description": "Unsupported media type"},
        413: {"description": "File exceeds size limit"},
    },
)
async def update_track(
    track_id: int,
    audio_file: UploadFile | None = OPTIONAL_AUDIO,
    cover_file: UploadFile | None = OPTIONAL_COVER,
    title: str | None = Form(default=None, min_length=1, max_length=255),
    description: str | None = Form(default=None),
    author: str | None = Form(default=None, max_length=255),
    latitude: float | None = Form(default=None, ge=-90, le=90),
    longitude: float | None = Form(default=None, ge=-180, le=180),
    location_name: str | None = Form(default=None, max_length=255),
    session: AsyncSession = Depends(get_session),
) -> TrackAdminDetail:
    repo = AudioTrackRepository(session)
    track = await repo.get_by_id(track_id)
    if track is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )

    storage = get_storage()
    old_audio_key: str | None = None
    old_cover_key: str | None = None

    if audio_file is not None and audio_file.filename:
        audio_ext, audio_content, audio_ct = await _read_and_validate_audio(audio_file)
        new_audio_key = f"tracks/{secrets.token_urlsafe(16)}{audio_ext}"
        storage.upload(new_audio_key, audio_content, audio_ct)
        old_audio_key = track.audio_s3_key
        track.audio_s3_key = new_audio_key

    if cover_file is not None and cover_file.filename:
        cover_ext, cover_content, cover_ct = await _read_and_validate_cover(cover_file)
        new_cover_key = f"covers/{secrets.token_urlsafe(16)}{cover_ext}"
        storage.upload(new_cover_key, cover_content, cover_ct)
        old_cover_key = track.cover_s3_key
        track.cover_s3_key = new_cover_key

    if title is not None:
        track.title = title.strip()
    if description is not None:
        track.description = description
    if author is not None:
        track.author = author
    if latitude is not None:
        track.latitude = latitude
    if longitude is not None:
        track.longitude = longitude
    if location_name is not None:
        track.location_name = location_name

    track = await repo.update(track)

    if old_audio_key:
        storage.delete(old_audio_key)
    if old_cover_key:
        storage.delete(old_cover_key)

    audio_url, cover_url = _presign_urls(track)
    return _to_detail(track, audio_url, cover_url)


@router.delete(
    "/{track_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a track (admin)",
    responses={404: {"description": "Track not found"}},
)
async def delete_track(
    track_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    repo = AudioTrackRepository(session)
    track = await repo.get_by_id(track_id)
    if track is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )
    storage = get_storage()
    storage.delete(track.audio_s3_key)
    if track.cover_s3_key:
        storage.delete(track.cover_s3_key)
    await repo.delete(track)
