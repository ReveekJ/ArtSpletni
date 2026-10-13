from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.user_progress import UserProgress


class ProgressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def is_completed(self, user_id: int, route_stop_id: int) -> bool:
        stmt = select(UserProgress.id).where(
            UserProgress.user_id == user_id,
            UserProgress.route_stop_id == route_stop_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none() is not None

    async def record_completion(self, user_id: int, route_stop_id: int) -> None:
        stmt = (
            insert(UserProgress)
            .values(
                user_id=user_id,
                route_stop_id=route_stop_id,
                completed_at=datetime.now(UTC),
            )
            .on_conflict_do_nothing(
                index_elements=[UserProgress.user_id, UserProgress.route_stop_id],
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_completed_stop_ids(self, user_id: int) -> set[int]:
        stmt = select(UserProgress.route_stop_id).where(
            UserProgress.user_id == user_id,
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return set(rows)
