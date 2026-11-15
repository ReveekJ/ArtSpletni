from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import and_, func, or_, select

from app.db.models import Route, RouteRun, RouteStop


class RouteRepository(SQLAlchemyAsyncRepository[Route]):
    model_type = Route

    async def published_active(self, moment: datetime) -> Sequence[Route]:
        return await self.get_many(
            Route.is_published.is_(True),
            or_(Route.active_from.is_(None), Route.active_from <= moment),
            or_(Route.active_until.is_(None), Route.active_until > moment),
            order_by=[(Route.created_at, False)],
        )

    async def published_with_point(self, point_id: UUID, moment: datetime) -> Sequence[Route]:
        stop_routes = select(RouteStop.route_id).where(RouteStop.point_id == point_id)
        return await self.get_many(
            Route.id.in_(stop_routes),
            Route.is_published.is_(True),
            and_(
                or_(Route.active_from.is_(None), Route.active_from <= moment),
                or_(Route.active_until.is_(None), Route.active_until > moment),
            ),
        )

    async def run_count(self, route_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(RouteRun).where(RouteRun.route_id == route_id)
        )
        return int(result.scalar_one())
