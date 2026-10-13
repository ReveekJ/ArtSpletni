from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.route_stop import RouteStop
from app.entities.route_stop_dependency import RouteStopDependency


class RouteStopRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, stop_id: int) -> RouteStop | None:
        return await self.session.get(RouteStop, stop_id)

    async def list_by_route(self, route_id: int) -> list[RouteStop]:
        stmt = (
            select(RouteStop)
            .where(RouteStop.route_id == route_id)
            .order_by(RouteStop.order_index)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def create(self, stop: RouteStop) -> RouteStop:
        self.session.add(stop)
        await self.session.commit()
        await self.session.refresh(stop)
        return stop

    async def update(self, stop: RouteStop) -> RouteStop:
        await self.session.commit()
        await self.session.refresh(stop)
        return stop

    async def delete(self, stop: RouteStop) -> None:
        await self.session.delete(stop)
        await self.session.commit()

    async def get_dependencies(self, stop_id: int) -> list[RouteStopDependency]:
        stmt = select(RouteStopDependency).where(
            RouteStopDependency.route_stop_id == stop_id,
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def add_dependency(self, stop_id: int, depends_on_id: int) -> None:
        dep = RouteStopDependency(
            route_stop_id=stop_id,
            depends_on_stop_id=depends_on_id,
        )
        self.session.add(dep)
        await self.session.commit()

    async def remove_dependency(self, stop_id: int, depends_on_id: int) -> None:
        await self.session.execute(
            delete(RouteStopDependency).where(
                RouteStopDependency.route_stop_id == stop_id,
                RouteStopDependency.depends_on_stop_id == depends_on_id,
            )
        )
        await self.session.commit()

    async def find_route_stops_for_track(self, track_id: int) -> list[RouteStop]:
        stmt = select(RouteStop).where(RouteStop.track_id == track_id)
        return list((await self.session.execute(stmt)).scalars().all())

    async def find_route_stops_for_checkpoint(
        self, checkpoint_id: int,
    ) -> list[RouteStop]:
        stmt = select(RouteStop).where(RouteStop.checkpoint_id == checkpoint_id)
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_all_dependencies_for_route(
        self, route_id: int,
    ) -> list[RouteStopDependency]:
        stmt = (
            select(RouteStopDependency)
            .join(RouteStop, RouteStop.id == RouteStopDependency.route_stop_id)
            .where(RouteStop.route_id == route_id)
        )
        return list((await self.session.execute(stmt)).scalars().all())
