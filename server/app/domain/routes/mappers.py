from app.db.models import Point, Route, RouteStop
from app.domain.i18n.schemas import localized_out
from app.domain.routes.admin_service import RouteAdminService
from app.domain.routes.schemas import (
    AdminRouteOut,
    AdminRouteSummary,
    AdminStopOut,
    IssueOut,
    StopPointOut,
)


class RouteAdminMapper:
    def __init__(self, service: RouteAdminService) -> None:
        self._service = service

    def summary(self, route: Route) -> AdminRouteSummary:
        return AdminRouteSummary(
            id=route.id,
            slug=route.slug,
            title=localized_out(route.title),
            ordering_mode=route.ordering_mode,
            is_published=route.is_published,
            stop_count=len(route.stops),
            updated_at=route.updated_at,
        )

    async def detail(self, route: Route) -> AdminRouteOut:
        points = await self._service.points_for(route)
        return AdminRouteOut(
            id=route.id,
            slug=route.slug,
            title=localized_out(route.title),
            description=localized_out(route.description),
            cover_asset_id=route.cover_asset_id,
            ordering_mode=route.ordering_mode,
            map_visibility=route.map_visibility,
            active_from=route.active_from,
            active_until=route.active_until,
            is_repeatable=route.is_repeatable,
            is_published=route.is_published,
            stops=[
                self._stop(stop, points[stop.point_id])
                for stop in sorted(route.stops, key=lambda item: item.position)
                if stop.point_id in points
            ],
            issues=[
                IssueOut(code=issue.code, stop_id=issue.stop_id) for issue in self._service.issues(route)
            ],
        )

    @staticmethod
    def _stop(stop: RouteStop, point: Point) -> AdminStopOut:
        return AdminStopOut(
            id=stop.id,
            point=StopPointOut(
                id=point.id,
                kind=point.kind,
                title=localized_out(point.title),
                latitude=point.latitude,
                longitude=point.longitude,
                is_published=point.is_published,
            ),
            position=stop.position,
            is_start=stop.is_start,
            is_required=stop.is_required,
            hint=localized_out(stop.hint),
            graph_x=stop.graph_x,
            graph_y=stop.graph_y,
            depends_on=[dep.depends_on_stop_id for dep in stop.dependencies],
        )
