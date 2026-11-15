from collections.abc import Sequence
from uuid import UUID

from app.db.models import MediaKind, OrderingMode, Point, Route, RouteStop, RouteStopDependency
from app.domain.i18n.services import TranslationService
from app.domain.media.services import MediaService
from app.domain.points.repositories import PointRepository
from app.domain.routes import progress
from app.domain.routes.repositories import RouteRepository
from app.domain.routes.schemas import RouteInput, StopInput, StopUpdate
from app.lib.exceptions import BadRequestError, ConflictError, NotFoundError
from app.lib.i18n import LocalizedText


class RouteAdminService:
    def __init__(
        self,
        routes: RouteRepository,
        points: PointRepository,
        media: MediaService,
        translator: TranslationService,
    ) -> None:
        self._routes = routes
        self._points = points
        self._media = media
        self._translator = translator

    async def list_all(self) -> Sequence[Route]:
        return await self._routes.get_many(order_by=[(Route.updated_at, True)])

    async def get(self, route_id: UUID) -> Route:
        route = await self._routes.get_one_or_none(id=route_id)
        if route is None:
            raise NotFoundError("Route not found", code="route_not_found")
        return route

    async def points_for(self, route: Route) -> dict[UUID, Point]:
        point_ids = [stop.point_id for stop in route.stops]
        return {point.id: point for point in await self._points.get_many(Point.id.in_(point_ids))}

    def issues(self, route: Route) -> list[progress.RouteIssue]:
        return progress.validate(route.ordering_mode, progress.nodes_of(route))

    async def create(self, data: RouteInput) -> Route:
        await self._ensure_slug_free(data.slug, None)
        route = Route(slug=data.slug, title={}, stops=[])
        await self._apply(route, data)
        return await self._routes.add(route)

    async def update(self, route_id: UUID, data: RouteInput) -> Route:
        route = await self.get(route_id)
        await self._ensure_slug_free(data.slug, route.id)
        await self._apply(route, data)
        return await self._save(route)

    async def delete(self, route_id: UUID) -> None:
        route = await self.get(route_id)
        if await self._routes.run_count(route.id):
            raise ConflictError("Route has player progress; unpublish it instead", code="route_has_runs")
        await self._routes.delete(route.id)

    async def set_published(self, route_id: UUID, published: bool) -> Route:
        route = await self.get(route_id)
        route.is_published = published
        return await self._save(route)

    async def add_stop(self, route_id: UUID, data: StopInput) -> Route:
        route = await self.get(route_id)
        if await self._points.get_one_or_none(id=data.point_id) is None:
            raise NotFoundError("Point not found", code="point_not_found")
        if any(stop.point_id == data.point_id for stop in route.stops):
            raise ConflictError("Point is already in this route", code="stop_exists")
        route.stops.append(
            RouteStop(
                point_id=data.point_id,
                position=max((stop.position for stop in route.stops), default=-1) + 1,
                is_start=data.is_start,
                is_required=data.is_required,
                hint=await self._localize_optional(data.hint, None),
                dependencies=[],
            )
        )
        return await self._save(route)

    async def update_stop(self, route_id: UUID, stop_id: UUID, data: StopUpdate) -> Route:
        route = await self.get(route_id)
        stop = self._stop(route, stop_id)
        if data.is_start is not None:
            stop.is_start = data.is_start
        if data.is_required is not None:
            stop.is_required = data.is_required
        if data.hint is not None:
            stop.hint = await self._localize_optional(data.hint, stop.hint)
        if data.graph_x is not None:
            stop.graph_x = data.graph_x
        if data.graph_y is not None:
            stop.graph_y = data.graph_y
        return await self._save(route)

    async def remove_stop(self, route_id: UUID, stop_id: UUID) -> Route:
        route = await self.get(route_id)
        stop = self._stop(route, stop_id)
        route.stops.remove(stop)
        for other in route.stops:
            other.dependencies = [dep for dep in other.dependencies if dep.depends_on_stop_id != stop_id]
        for position, other in enumerate(sorted(route.stops, key=lambda item: item.position)):
            other.position = position
        return await self._save(route)

    async def reorder(self, route_id: UUID, stop_ids: list[UUID]) -> Route:
        route = await self.get(route_id)
        if sorted(stop_ids) != sorted(stop.id for stop in route.stops):
            raise BadRequestError("Order must list every stop exactly once", code="invalid_order")
        positions = {stop_id: index for index, stop_id in enumerate(stop_ids)}
        for stop in route.stops:
            stop.position = positions[stop.id]
        return await self._save(route)

    async def add_dependency(self, route_id: UUID, stop_id: UUID, depends_on_id: UUID) -> Route:
        route = await self.get(route_id)
        if route.ordering_mode is not OrderingMode.GRAPH:
            raise BadRequestError("Dependencies are only used in graph mode", code="not_graph_mode")
        stop = self._stop(route, stop_id)
        self._stop(route, depends_on_id)
        if stop_id == depends_on_id:
            raise BadRequestError("A stop cannot depend on itself", code="self_dependency")
        if any(dep.depends_on_stop_id == depends_on_id for dep in stop.dependencies):
            return route
        stop.dependencies.append(RouteStopDependency(depends_on_stop_id=depends_on_id))
        if progress.find_cycle(progress.nodes_of(route)) is not None:
            raise ConflictError("Dependency would create a cycle", code="dependency_cycle")
        return await self._save(route)

    async def remove_dependency(self, route_id: UUID, stop_id: UUID, depends_on_id: UUID) -> Route:
        route = await self.get(route_id)
        stop = self._stop(route, stop_id)
        stop.dependencies = [dep for dep in stop.dependencies if dep.depends_on_stop_id != depends_on_id]
        return await self._save(route)

    async def _save(self, route: Route) -> Route:
        if route.is_published and self.issues(route):
            raise ConflictError("Route is invalid and cannot be published", code="route_invalid")
        return await self._routes.update(route, auto_refresh=False)

    async def _apply(self, route: Route, data: RouteInput) -> None:
        if data.active_from and data.active_until and data.active_from >= data.active_until:
            raise BadRequestError("Active period is empty", code="invalid_period")
        title = await self._translator.localize(data.title, route.title or None)
        if title is None:
            raise BadRequestError("Title is required", code="title_required")
        route.slug = data.slug
        route.title = title
        route.description = await self._localize_optional(data.description, route.description)
        if data.cover_asset_id is not None:
            await self._media.get_ready(data.cover_asset_id, MediaKind.IMAGE)
        route.cover_asset_id = data.cover_asset_id
        route.ordering_mode = data.ordering_mode
        route.map_visibility = data.map_visibility
        route.active_from = data.active_from
        route.active_until = data.active_until
        route.is_repeatable = data.is_repeatable

    async def _localize_optional(
        self, submitted: dict[str, str] | None, previous: LocalizedText | None
    ) -> LocalizedText | None:
        if submitted is None:
            return None
        return await self._translator.localize(submitted, previous, required=False)

    async def _ensure_slug_free(self, slug: str, route_id: UUID | None) -> None:
        existing = await self._routes.get_one_or_none(slug=slug)
        if existing is not None and existing.id != route_id:
            raise ConflictError("Slug is already used", code="slug_taken")

    @staticmethod
    def _stop(route: Route, stop_id: UUID) -> RouteStop:
        for stop in route.stops:
            if stop.id == stop_id:
                return stop
        raise NotFoundError("Stop not found in this route", code="stop_not_found")
