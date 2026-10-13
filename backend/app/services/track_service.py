import secrets
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.audio_track import AudioTrack
from app.entities.track_localization import TrackLocalization
from app.repositories.audio_track_repo import AudioTrackRepository
from app.repositories.track_localization_repo import TrackLocalizationRepository
from app.services.storage_service import StorageService

PUBLISHED_STATUS = "published"
SUPPORTED_LANGUAGES: tuple[str, ...] = ("ru", "en", "zh")
DEFAULT_LANGUAGE = "ru"


@dataclass(slots=True)
class TrackDTO:
    slug: str
    title: str
    description: str | None
    author: str | None
    audio_url: str
    cover_url: str | None
    latitude: float
    longitude: float
    location_name: str | None


class TrackService:
    def __init__(self, session: AsyncSession, storage: StorageService) -> None:
        self.repo = AudioTrackRepository(session)
        self.localization_repo = TrackLocalizationRepository(session)
        self.storage = storage

    async def get_published_by_slug(
        self, slug: str, presign_ttl_seconds: int | None = None, language: str = DEFAULT_LANGUAGE
    ) -> TrackDTO | None:
        track = await self.repo.get_by_slug(slug)
        if track is None or track.moderation_status != PUBLISHED_STATUS:
            return None
        resolved_language = self.resolve_language(language)
        localization: TrackLocalization | None = None
        if resolved_language != DEFAULT_LANGUAGE:
            localization = await self.localization_repo.get_by_track_and_language(
                track.id, resolved_language
            )
        return self._to_dto(track, presign_ttl_seconds, localization)

    async def get_track_entity_by_slug(self, slug: str) -> AudioTrack | None:
        return await self.repo.get_by_slug(slug)

    def _to_dto(
        self,
        track: AudioTrack,
        presign_ttl_seconds: int | None = None,
        localization: TrackLocalization | None = None,
    ) -> TrackDTO:
        if localization is not None:
            audio_key = localization.audio_s3_key or track.audio_s3_key
            cover_key = localization.cover_s3_key or track.cover_s3_key
            return TrackDTO(
                slug=track.slug,
                title=localization.title,
                description=localization.description,
                author=track.author,
                audio_url=self.storage.presign_get(audio_key, presign_ttl_seconds),
                cover_url=(
                    self.storage.presign_get(cover_key, presign_ttl_seconds)
                    if cover_key
                    else None
                ),
                latitude=track.latitude,
                longitude=track.longitude,
                location_name=localization.location_name,
            )
        return TrackDTO(
            slug=track.slug,
            title=track.title,
            description=track.description,
            author=track.author,
            audio_url=self.storage.presign_get(track.audio_s3_key, presign_ttl_seconds),
            cover_url=(
                self.storage.presign_get(track.cover_s3_key, presign_ttl_seconds)
                if track.cover_s3_key
                else None
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

    @staticmethod
    def resolve_language(language: str | None) -> str:
        if language is None:
            return DEFAULT_LANGUAGE
        normalized = language.strip().lower()[:2]
        if normalized in SUPPORTED_LANGUAGES:
            return normalized
        return DEFAULT_LANGUAGE
