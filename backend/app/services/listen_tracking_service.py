import re
from dataclasses import dataclass

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.listen_session import ListenSession
from app.entities.user import User
from app.repositories.audio_track_repo import AudioTrackRepository
from app.repositories.listen_session_repo import ListenSessionRepository
from app.services.track_service import PUBLISHED_STATUS

MOBILE_RE = re.compile(r"Mobile|Android|iPhone|iPod|Windows Phone", re.IGNORECASE)
TABLET_RE = re.compile(r"iPad|Android(?!.*Mobile)|Tablet", re.IGNORECASE)

DEVICE_TYPES = ("desktop", "mobile", "tablet")


@dataclass(slots=True)
class ListenSessionInput:
    slug: str
    session_token: str
    visitor_id: str
    track_duration_seconds: float | None
    listened_seconds: float
    last_position_seconds: float
    seek_count: int
    is_completed: bool
    referrer: str | None
    language: str | None


class ListenTrackingService:
    def __init__(self, session: AsyncSession) -> None:
        self.tracks = AudioTrackRepository(session)
        self.sessions = ListenSessionRepository(session)

    async def record(
        self, payload: ListenSessionInput, device_type: str | None,
        request: Request | None = None,
    ) -> bool:
        """Persist a listen session. Returns False when the track is unknown or unpublished."""
        track = await self.tracks.get_by_slug(payload.slug)
        if track is None or track.moderation_status != PUBLISHED_STATUS:
            return False

        completion_ratio = self._completion_ratio(
            payload.listened_seconds,
            payload.track_duration_seconds,
        )
        is_completed = payload.is_completed or (
            completion_ratio is not None and completion_ratio >= 0.95
        )

        entity = ListenSession(
            track_id=track.id,
            session_token=payload.session_token,
            visitor_id=payload.visitor_id,
            track_duration_seconds=payload.track_duration_seconds,
            listened_seconds=payload.listened_seconds,
            last_position_seconds=payload.last_position_seconds,
            completion_ratio=completion_ratio,
            seek_count=payload.seek_count,
            is_completed=is_completed,
            referrer=payload.referrer,
            language=payload.language,
            device_type=device_type,
        )
        await self.sessions.upsert(entity)

        await self._try_record_route_progress(
            track.id, completion_ratio, is_completed, request,
        )
        return True

    @staticmethod
    def _completion_ratio(listened: float, duration: float | None) -> float | None:
        if duration is None or duration <= 0:
            return None
        return min(listened / duration, 1.0)

    @staticmethod
    def parse_device_type(user_agent: str | None) -> str | None:
        if not user_agent:
            return None
        if TABLET_RE.search(user_agent):
            return "tablet"
        if MOBILE_RE.search(user_agent):
            return "mobile"
        return "desktop"

    async def _try_record_route_progress(
        self,
        track_id: int,
        completion_ratio: float | None,
        is_completed: bool,
        request: Request | None,
    ) -> None:
        if request is None:
            return
        user_id = request.session.get("user_id")
        if not user_id:
            return
        from app.services.auth_service import AuthService
        from app.services.progress_service import ProgressService

        user: User | None = await AuthService(self.tracks.session).get_by_id(user_id)
        if user is None:
            return
        progress_service = ProgressService(self.tracks.session)
        await progress_service.check_and_record_listen_progress(
            user, track_id, completion_ratio, is_completed,
        )
        return "desktop"
