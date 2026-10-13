from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.entities.route import Route
from app.entities.route_stop import RouteStop


class RouteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_slug(self, slug: str) -> Route | None:
        stmt = select(Route).where(Route.slug == slug)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, route_id: int) -> Route | None:
        return await self.session.get(Route, route_id)

    async def list_published(self) -> list[Route]:
        stmt = select(Route).where(Route.is_published.is_(True)).order_by(Route.id)
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_all(self) -> list[Route]:
        stmt = select(Route).order_by(Route.id.desc())
        return list((await self.session.execute(stmt)).scalars().all())

    async def create(self, route: Route) -> Route:
        self.session.add(route)
        await self.session.commit()
        await self.session.refresh(route)
        return route

    async def update(self, route: Route) -> Route:
        await self.session.commit()
        await self.session.refresh(route)
        return route

    async def delete(self, route: Route) -> None:
        await self.session.delete(route)
        await self.session.commit()

    async def get_stops(self, route_id: int) -> list[RouteStop]:
        stmt = (
            select(RouteStop)
            .where(RouteStop.route_id == route_id)
            .order_by(RouteStop.order_index)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_route_with_stops(self, route_id: int) -> Route | None:
        stmt = (
            select(Route)
            .options(selectinload(Route.stops))
            .where(Route.id == route_id)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()
