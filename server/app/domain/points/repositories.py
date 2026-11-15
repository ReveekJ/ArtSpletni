from collections.abc import Sequence
from uuid import UUID

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Point, RouteStop, Unlock


class PointRepository(SQLAlchemyAsyncRepository[Point]):
    model_type = Point

    async def route_usage_count(self, point_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(RouteStop).where(RouteStop.point_id == point_id)
        )
        return int(result.scalar_one())


class UnlockRepository(SQLAlchemyAsyncRepository[Unlock]):
    model_type = Unlock

    async def ensure(self, user_id: UUID, point_id: UUID) -> bool:
        statement = (
            insert(Unlock)
            .values(user_id=user_id, point_id=point_id)
            .on_conflict_do_nothing(index_elements=[Unlock.user_id, Unlock.point_id])
            .returning(Unlock.id)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def for_user(self, user_id: UUID) -> Sequence[Unlock]:
        return await self.get_many(Unlock.user_id == user_id, order_by=[(Unlock.created_at, True)])

    async def unlocked_point_ids(self, user_id: UUID, point_ids: set[UUID]) -> set[UUID]:
        if not point_ids:
            return set()
        result = await self.session.execute(
            select(Unlock.point_id).where(Unlock.user_id == user_id, Unlock.point_id.in_(point_ids))
        )
        return set(result.scalars())
