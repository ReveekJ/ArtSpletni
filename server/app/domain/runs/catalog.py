from collections.abc import Sequence
from uuid import UUID

from app.db.models import MapVisibility, Point, Route, RouteRun, RouteStop, RunStatus, User
from app.domain.media.services import MediaService
from app.domain.points.repositories import PointRepository
from app.domain.routes.repositories import RouteRepository
from app.domain.runs.repositories import RunRepository
from app.domain.runs.schemas import (
    MapStopOut,
    RouteMapOut,
    RouteSummaryOut,
    RunPresenter,
    RunStateOut,
    StopState,
)
from app.domain.runs.services import available_in_run, utcnow
from app.lib.exceptions import NotFoundError
from app.lib.i18n import resolve_text

LIVE_STATUSES = (RunStatus.ACTIVE, RunStatus.PAUSED)


class RouteCatalogService:
    def __init__(
        self,
        routes: RouteRepository,
        points: PointRepository,
        runs: RunRepository,
        media: MediaService,
        presenter: RunPresenter,
    ) -> None:
        self._routes = routes
        self._points = points
        self._runs = runs
        self._media = media
        self._presenter = presenter

    async def list_all(self, user: User | None) -> list[RouteSummaryOut]:
        routes = await self._routes.published_active(utcnow())
        runs = await self._runs.for_user(user.id) if user else []
        return [await self._summary(route, self._current_run(route, runs)) for route in routes]

    async def my_runs(self, user: User) -> list[RunStateOut]:
        runs = await self._runs.for_user(user.id)
        routes = {
            route.id: route
            for route in await self._routes.get_many(Route.id.in_({run.route_id for run in runs}))
        }
        return [
            self._presenter.run_state(routes[run.route_id], run) for run in runs if run.route_id in routes
        ]

    async def route_map(self, slug: str, user: User | None) -> RouteMapOut:
        route = next(
            (item for item in await self._routes.published_active(utcnow()) if item.slug == slug), None
        )
        if route is None:
            raise NotFoundError("Route not found", code="route_not_found")
        runs = await self._runs.for_user_route(user.id, route.id) if user else []
        run = self._current_run(route, runs)
        visited = run.visited_stop_ids if run else set()
        available = available_in_run(route, run) if run is None or run.status in LIVE_STATUSES else set()
        points = {
            point.id: point
            for point in await self._points.get_many(Point.id.in_([stop.point_id for stop in route.stops]))
        }
        stops = [
            self._map_stop(route, stop, points.get(stop.point_id), visited, available) for stop in route.stops
        ]
        return RouteMapOut(route=await self._summary(route, run), stops=stops)

    def _map_stop(
        self,
        route: Route,
        stop: RouteStop,
        point: Point | None,
        visited: set[UUID],
        available: set[UUID],
    ) -> MapStopOut:
        if stop.id in visited:
            state = StopState.VISITED
        elif stop.id in available:
            state = StopState.AVAILABLE
        else:
            state = StopState.LOCKED
        show_point = point is not None and (
            route.map_visibility is MapVisibility.ALL
            or state is StopState.VISITED
            or (state is StopState.AVAILABLE and route.map_visibility is MapVisibility.PROGRESSIVE)
        )
        show_hint = state is StopState.AVAILABLE or route.map_visibility is MapVisibility.ALL
        visible_point = point if show_point else None
        return MapStopOut(
            stop_id=stop.id,
            position=stop.position,
            state=state,
            is_start=stop.is_start,
            is_required=stop.is_required,
            point_id=visible_point.id if visible_point else None,
            kind=visible_point.kind if visible_point else None,
            title=resolve_text(visible_point.title, self._presenter.language, self._presenter.fallback)
            if visible_point
            else None,
            latitude=visible_point.latitude if visible_point else None,
            longitude=visible_point.longitude if visible_point else None,
            hint=resolve_text(stop.hint, self._presenter.language, self._presenter.fallback)
            if show_hint
            else None,
        )

    async def _summary(self, route: Route, run: RouteRun | None) -> RouteSummaryOut:
        cover = (
            (await self._media.get_many({route.cover_asset_id})).get(route.cover_asset_id)
            if route.cover_asset_id
            else None
        )
        return RouteSummaryOut(
            id=route.id,
            slug=route.slug,
            title=self._presenter.title(route),
            description=resolve_text(route.description, self._presenter.language, self._presenter.fallback),
            cover_url=await self._media.download_url(cover) if cover else None,
            ordering_mode=route.ordering_mode,
            map_visibility=route.map_visibility,
            stop_count=len(route.stops),
            active_until=route.active_until,
            run=self._presenter.run_state(route, run) if run else None,
        )

    @staticmethod
    def _current_run(route: Route, runs: Sequence[RouteRun]) -> RouteRun | None:
        own = [run for run in runs if run.route_id == route.id]
        live = next((run for run in own if run.status in LIVE_STATUSES), None)
        if live is not None:
            return live
        return next((run for run in own if run.status is RunStatus.COMPLETED), None)
