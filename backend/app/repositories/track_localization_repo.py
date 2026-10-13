from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.track_localization import TrackLocalization


class TrackLocalizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_track_and_language(
        self, track_id: int, language: str
    ) -> TrackLocalization | None:
        stmt = select(TrackLocalization).where(
            TrackLocalization.track_id == track_id,
            TrackLocalization.language == language,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_track(self, track_id: int) -> list[TrackLocalization]:
        stmt = select(TrackLocalization).where(
            TrackLocalization.track_id == track_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, localization: TrackLocalization) -> TrackLocalization:
        self.session.add(localization)
        await self.session.commit()
        await self.session.refresh(localization)
        return localization

    async def update(self, localization: TrackLocalization) -> TrackLocalization:
        await self.session.commit()
        await self.session.refresh(localization)
        return localization

    async def delete(self, localization: TrackLocalization) -> None:
        await self.session.delete(localization)
        await self.session.commit()
