import secrets
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.audio_track import AudioTrack
from app.entities.checkpoint import Checkpoint
from app.entities.route import Route
from app.entities.route_stop import RouteStop
from app.repositories.route_repo import RouteRepository
from app.repositories.route_stop_repo import RouteStopRepository
from app.services.storage_service import StorageService


@dataclass(slots=True)
class StopDTO:
    id: int
    order_index: int
    stop_type: str
    track_id: int | None
    checkpoint_id: int | None
    completion_criteria: str
    title: str
    slug: str
    latitude: float
    longitude: float
    location_name: str | None
    depends_on: list[int]


@dataclass(slots=True)
class RouteDTO:
    id: int
    slug: str
    title: str
    description: str | None
    cover_url: str | None
    is_published: bool
    stops: list[StopDTO]


@dataclass(slots=True)
class RouteSummaryDTO:
    id: int
    slug: str
    title: str
    description: str | None
    cover_url: str | None


class RouteService:
    def __init__(self, session: AsyncSession, storage: StorageService) -> None:
        self.session = session
        self.repo = RouteRepository(session)
        self.stop_repo = RouteStopRepository(session)
        self.storage = storage

    async def list_published(self) -> list[RouteSummaryDTO]:
        routes = await self.repo.list_published()
        return [
            RouteSummaryDTO(
                id=r.id,
                slug=r.slug,
                title=r.title,
                description=r.description,
                cover_url=(
                    self.storage.presign_get(r.cover_s3_key, 3600)
                    if r.cover_s3_key
                    else None
                ),
            )
            for r in routes
        ]

    async def get_published_by_slug(self, slug: str) -> RouteDTO | None:
        route = await self.repo.get_by_slug(slug)
        if route is None or not route.is_published:
            return None
        return await self._to_dto(route)

    async def get_by_id(self, route_id: int) -> RouteDTO | None:
        route = await self.repo.get_by_id(route_id)
        if route is None:
            return None
        return await self._to_dto(route)

    async def list_all(self) -> list[RouteSummaryDTO]:
        routes = await self.repo.list_all()
        return [
            RouteSummaryDTO(
                id=r.id,
                slug=r.slug,
                title=r.title,
                description=r.description,
                cover_url=(
                    self.storage.presign_get(r.cover_s3_key, 3600)
                    if r.cover_s3_key
                    else None
                ),
            )
            for r in routes
        ]

    async def create(
        self,
        title: str,
        description: str | None,
        cover_s3_key: str | None,
    ) -> Route:
        route = Route(
            slug=self.generate_slug(),
            title=title,
            description=description,
            cover_s3_key=cover_s3_key,
            is_published=False,
        )
        return await self.repo.create(route)

    async def update(
        self,
        route: Route,
        title: str | None,
        description: str | None,
        is_published: bool | None,
        cover_s3_key: str | None,
    ) -> Route:
        if title is not None:
            route.title = title
        if description is not None:
            route.description = description
        if is_published is not None:
            route.is_published = is_published
        if cover_s3_key is not None:
            route.cover_s3_key = cover_s3_key
        return await self.repo.update(route)

    async def delete(self, route: Route) -> None:
        if route.cover_s3_key:
            self.storage.delete(route.cover_s3_key)
        await self.repo.delete(route)

    async def add_stop(
        self,
        route_id: int,
        stop_type: str,
        track_id: int | None,
        checkpoint_id: int | None,
        completion_criteria: str,
    ) -> RouteStop:
        existing_stops = await self.stop_repo.list_by_route(route_id)
        next_order = max((s.order_index for s in existing_stops), default=-1) + 1
        stop = RouteStop(
            route_id=route_id,
            order_index=next_order,
            stop_type=stop_type,
            track_id=track_id,
            checkpoint_id=checkpoint_id,
            completion_criteria=completion_criteria,
        )
        return await self.stop_repo.create(stop)

    async def update_stop(
        self,
        stop: RouteStop,
        completion_criteria: str | None,
        order_index: int | None,
    ) -> RouteStop:
        if completion_criteria is not None:
            stop.completion_criteria = completion_criteria
        if order_index is not None:
            stop.order_index = order_index
        return await self.stop_repo.update(stop)

    async def delete_stop(self, stop: RouteStop) -> None:
        await self.stop_repo.delete(stop)

    async def add_dependency(self, stop_id: int, depends_on_id: int) -> None:
        if stop_id == depends_on_id:
            raise ValueError("A stop cannot depend on itself")
        existing_deps = await self.stop_repo.get_dependencies(stop_id)
        if any(d.depends_on_stop_id == depends_on_id for d in existing_deps):
            raise ValueError("Dependency already exists")
        if await self._creates_cycle(stop_id, depends_on_id):
            raise ValueError("This dependency would create a cycle")
        try:
            await self.stop_repo.add_dependency(stop_id, depends_on_id)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValueError("Dependency already exists") from exc

    async def remove_dependency(self, stop_id: int, depends_on_id: int) -> None:
        await self.stop_repo.remove_dependency(stop_id, depends_on_id)

    async def reorder_stops(self, route_id: int, stop_ids: list[int]) -> None:
        for index, stop_id in enumerate(stop_ids):
            stop = await self.stop_repo.get_by_id(stop_id)
            if stop is None or stop.route_id != route_id:
                continue
            stop.order_index = index
            await self.stop_repo.update(stop)

    async def find_stops_for_track(self, track_id: int) -> list[RouteStop]:
        return await self.stop_repo.find_route_stops_for_track(track_id)

    async def find_stops_for_checkpoint(self, checkpoint_id: int) -> list[RouteStop]:
        return await self.stop_repo.find_route_stops_for_checkpoint(checkpoint_id)

    async def _creates_cycle(self, stop_id: int, depends_on_id: int) -> bool:
        visited: set[int] = set()
        stack = [depends_on_id]
        while stack:
            current = stack.pop()
            if current == stop_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            deps = await self.stop_repo.get_dependencies(current)
            for dep in deps:
                stack.append(dep.depends_on_stop_id)
        return False

    async def _to_dto(self, route: Route) -> RouteDTO:
        stops = await self.stop_repo.list_by_route(route.id)
        all_deps = await self.stop_repo.get_all_dependencies_for_route(route.id)
        deps_map: dict[int, list[int]] = {}
        for dep in all_deps:
            deps_map.setdefault(dep.route_stop_id, []).append(dep.depends_on_stop_id)

        stop_dtos: list[StopDTO] = []
        for stop in stops:
            title = ""
            slug = ""
            lat: float = 0.0
            lng: float = 0.0
            loc_name: str | None = None
            if stop.track_id is not None:
                track = await self.session.get(AudioTrack, stop.track_id)
                if track:
                    title = track.title
                    slug = track.slug
                    lat = track.latitude
                    lng = track.longitude
                    loc_name = track.location_name
            elif stop.checkpoint_id is not None:
                cp = await self.session.get(Checkpoint, stop.checkpoint_id)
                if cp:
                    title = cp.title
                    slug = cp.slug
                    lat = cp.latitude
                    lng = cp.longitude
                    loc_name = cp.location_name
            stop_dtos.append(
                StopDTO(
                    id=stop.id,
                    order_index=stop.order_index,
                    stop_type=stop.stop_type,
                    track_id=stop.track_id,
                    checkpoint_id=stop.checkpoint_id,
                    completion_criteria=stop.completion_criteria,
                    title=title,
                    slug=slug,
                    latitude=lat,
                    longitude=lng,
                    location_name=loc_name,
                    depends_on=deps_map.get(stop.id, []),
                )
            )
        return RouteDTO(
            id=route.id,
            slug=route.slug,
            title=route.title,
            description=route.description,
            cover_url=(
                self.storage.presign_get(route.cover_s3_key, 3600)
                if route.cover_s3_key
                else None
            ),
            is_published=route.is_published,
            stops=stop_dtos,
        )

    @staticmethod
    def generate_slug() -> str:
        return secrets.token_urlsafe(8)
