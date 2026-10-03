import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.audio_track import AudioTrack
from app.entities.track_access_grant import TrackAccessGrant
from app.services.track_service import PUBLISHED_STATUS


class TrackAccessService:
    def __init__(self, session: AsyncSession, ttl_seconds: int) -> None:
        self.session = session
        self.ttl_seconds = ttl_seconds

    async def create_grant(self, track: AudioTrack) -> str:
        secret = secrets.token_urlsafe(32)
        grant = TrackAccessGrant(
            track_id=track.id,
            secret_hash=self._hash_secret(secret),
            expires_at=self._expires_at(),
        )
        self.session.add(grant)
        await self.session.execute(
            delete(TrackAccessGrant).where(
                TrackAccessGrant.track_id == track.id,
                TrackAccessGrant.expires_at < datetime.now(UTC),
            )
        )
        await self.session.commit()
        return secret

    async def is_granted(self, slug: str, secret: str | None) -> bool:
        if not secret:
            return False
        stmt = (
            select(TrackAccessGrant.id)
            .join(AudioTrack, AudioTrack.id == TrackAccessGrant.track_id)
            .where(
                AudioTrack.slug == slug,
                AudioTrack.moderation_status == PUBLISHED_STATUS,
                TrackAccessGrant.secret_hash == self._hash_secret(secret),
                TrackAccessGrant.revoked_at.is_(None),
                TrackAccessGrant.expires_at > datetime.now(UTC),
            )
        )
        return (await self.session.execute(stmt)).scalar_one_or_none() is not None

    def _expires_at(self) -> datetime:
        return datetime.now(UTC) + timedelta(seconds=self.ttl_seconds)

    @staticmethod
    def _hash_secret(secret: str) -> str:
        return hashlib.sha256(secret.encode("utf-8")).hexdigest()