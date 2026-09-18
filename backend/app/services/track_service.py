import secrets
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.audio_track import AudioTrack
from app.repositories.audio_track_repo import AudioTrackRepository
from app.services.storage_service import StorageService


@dataclass(slots=True)
class TrackDTO:
    slug: str
    title: str
    description: str | None
    author: str | None
    audio_url: str
    cover_url: str | None
    latitude: float | None
    longitude: float | None
    location_name: str | None


class TrackService:
    def __init__(self, session: AsyncSession, storage: StorageService) -> None:
        self.repo = AudioTrackRepository(session)
        self.storage = storage

    async def get_published_by_slug(self, slug: str) -> TrackDTO | None:
        track = await self.repo.get_by_slug(slug)
        if track is None or not track.is_published:
            return None
        return self._to_dto(track)

    def _to_dto(self, track: AudioTrack) -> TrackDTO:
        return TrackDTO(
            slug=track.slug,
            title=track.title,
            description=track.description,
            author=track.author,
            audio_url=self.storage.presign_get(track.audio_s3_key),
            cover_url=(
                self.storage.presign_get(track.cover_s3_key) if track.cover_s3_key else None
            ),
            latitude=track.latitude,
            longitude=track.longitude,
            location_name=track.location_name,
        )

    @staticmethod
    def generate_slug() -> str:
        return secrets.token_urlsafe(8)

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(UTC)
