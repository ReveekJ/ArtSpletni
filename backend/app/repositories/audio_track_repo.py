from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.audio_track import AudioTrack


class AudioTrackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_slug(self, slug: str) -> AudioTrack | None:
        stmt = select(AudioTrack).where(AudioTrack.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, track_id: int) -> AudioTrack | None:
        return await self.session.get(AudioTrack, track_id)

    async def list_all(self) -> list[AudioTrack]:
        result = await self.session.execute(select(AudioTrack).order_by(AudioTrack.id.desc()))
        return list(result.scalars().all())

    async def create(self, track: AudioTrack) -> AudioTrack:
        self.session.add(track)
        await self.session.commit()
        await self.session.refresh(track)
        return track

    async def update(self, track: AudioTrack) -> AudioTrack:
        await self.session.commit()
        await self.session.refresh(track)
        return track

    async def delete(self, track: AudioTrack) -> None:
        await self.session.delete(track)
        await self.session.commit()

    async def slug_exists(self, slug: str) -> bool:
        return await self.get_by_slug(slug) is not None
