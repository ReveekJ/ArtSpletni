from uuid import UUID

from litestar import Controller, delete, get, patch, post, put
from litestar.di import NamedDependency, Provide
from litestar.params import FromPath, JSONBody
from litestar.status_codes import HTTP_200_OK

from app.domain.auth.guards import requires_admin
from app.domain.routes.admin_service import RouteAdminService
from app.domain.routes.deps import provide_route_admin_service
from app.domain.routes.mappers import RouteAdminMapper
from app.domain.routes.schemas import (
    AdminRouteOut,
    AdminRouteSummary,
    DependencyInput,
    RouteInput,
    StopInput,
    StopOrderInput,
    StopUpdate,
)


async def provide_route_admin_mapper(
    route_admin_service: NamedDependency[RouteAdminService],
) -> RouteAdminMapper:
    return RouteAdminMapper(route_admin_service)


class AdminRouteController(Controller):
    path = "/api/admin/routes"
    tags = ["Admin: Routes"]
    guards = [requires_admin]
    dependencies = {
        "route_admin_service": Provide(provide_route_admin_service),
        "route_admin_mapper": Provide(provide_route_admin_mapper),
    }

    @get("/", summary="List routes", description="List all routes including drafts.")
    async def list_routes(
        self,
        route_admin_service: NamedDependency[RouteAdminService],
        route_admin_mapper: NamedDependency[RouteAdminMapper],
    ) -> list[AdminRouteSummary]:
        return [route_admin_mapper.summary(route) for route in await route_admin_service.list_all()]

    @post("/", summary="Create route", description="Create a draft route.")
    async def create_route(
        self,
        data: JSONBody[RouteInput],
        route_admin_service: NamedDependency[RouteAdminService],
        route_admin_mapper: NamedDependency[RouteAdminMapper],
    ) -> AdminRouteOut:
        return await route_admin_mapper.detail(await route_admin_service.create(data))

    @get(
        "/{route_id:uuid}",
        summary="Get route",
        description="Route with stops, dependencies and validation issues.",
    )
    async def get_route(
        self,
        route_id: FromPath[UUID],
        route_admin_service: NamedDependency[RouteAdminService],
        route_admin_mapper: NamedDependency[RouteAdminMapper],
    ) -> AdminRouteOut:
        return await route_admin_mapper.detail(await route_admin_service.get(route_id))

    @put("/{route_id:uuid}", summary="Update route", description="Update route settings.")
    async def update_route(
        self,
        route_id: FromPath[UUID],
        data: JSONBody[RouteInput],
        route_admin_service: NamedDependency[RouteAdminService],
        route_admin_mapper: NamedDependency[RouteAdminMapper],
    ) -> AdminRouteOut:
        return await route_admin_mapper.detail(await route_admin_service.update(route_id, data))

    @delete("/{route_id:uuid}", summary="Delete route", description="Delete a route without player progress.")
    async def delete_route(
        self, route_id: FromPath[UUID], route_admin_service: NamedDependency[RouteAdminService]
    ) -> None:
        await route_admin_service.delete(route_id)

    @post(
        "/{route_id:uuid}/publish",
        summary="Publish route",
        description="Publish a route; fails with route_invalid while validation issues exist.",
        status_code=HTTP_200_OK,
    )
    async def publish_route(
        self,
        route_id: FromPath[UUID],
        route_admin_service: NamedDependency[RouteAdminService],
        route_admin_mapper: NamedDependency[RouteAdminMapper],
    ) -> AdminRouteOut:
        return await route_admin_mapper.detail(await route_admin_service.set_published(route_id, True))

    @post(
        "/{route_id:uuid}/unpublish",
        summary="Unpublish route",
        description="Hide a route from players.",
        status_code=HTTP_200_OK,
    )
    async def unpublish_route(
        self,
        route_id: FromPath[UUID],
        route_admin_service: NamedDependency[RouteAdminService],
        route_admin_mapper: NamedDependency[RouteAdminMapper],
    ) -> AdminRouteOut:
        return await route_admin_mapper.detail(await route_admin_service.set_published(route_id, False))

    @post("/{route_id:uuid}/stops", summary="Add stop", description="Append a point to the route.")
    async def add_stop(
        self,
        route_id: FromPath[UUID],
        data: JSONBody[StopInput],
        route_admin_service: NamedDependency[RouteAdminService],
        route_admin_mapper: NamedDependency[RouteAdminMapper],
    ) -> AdminRouteOut:
        return await route_admin_mapper.detail(await route_admin_service.add_stop(route_id, data))

    @patch(
        "/{route_id:uuid}/stops/{stop_id:uuid}",
        summary="Update stop",
        description="Change start/required flags, hint or graph position of a stop.",
    )
    async def update_stop(
        self,
        route_id: FromPath[UUID],
        stop_id: FromPath[UUID],
        data: JSONBody[StopUpdate],
        route_admin_service: NamedDependency[RouteAdminService],
        route_admin_mapper: NamedDependency[RouteAdminMapper],
    ) -> AdminRouteOut:
        return await route_admin_mapper.detail(await route_admin_service.update_stop(route_id, stop_id, data))

    @delete(
        "/{route_id:uuid}/stops/{stop_id:uuid}",
        summary="Remove stop",
        description="Remove a stop and its dependency edges.",
        status_code=HTTP_200_OK,
    )
    async def remove_stop(
        self,
        route_id: FromPath[UUID],
        stop_id: FromPath[UUID],
        route_admin_service: NamedDependency[RouteAdminService],
        route_admin_mapper: NamedDependency[RouteAdminMapper],
    ) -> AdminRouteOut:
        return await route_admin_mapper.detail(await route_admin_service.remove_stop(route_id, stop_id))

    @put("/{route_id:uuid}/stops/order", summary="Reorder stops", description="Set the order of all stops.")
    async def reorder_stops(
        self,
        route_id: FromPath[UUID],
        data: JSONBody[StopOrderInput],
        route_admin_service: NamedDependency[RouteAdminService],
        route_admin_mapper: NamedDependency[RouteAdminMapper],
    ) -> AdminRouteOut:
        return await route_admin_mapper.detail(await route_admin_service.reorder(route_id, data.stop_ids))

    @post(
        "/{route_id:uuid}/stops/{stop_id:uuid}/dependencies",
        summary="Add dependency",
        description="Require another stop to be visited first (graph mode only, cycles rejected).",
    )
    async def add_dependency(
        self,
        route_id: FromPath[UUID],
        stop_id: FromPath[UUID],
        data: JSONBody[DependencyInput],
        route_admin_service: NamedDependency[RouteAdminService],
        route_admin_mapper: NamedDependency[RouteAdminMapper],
    ) -> AdminRouteOut:
        route = await route_admin_service.add_dependency(route_id, stop_id, data.depends_on_stop_id)
        return await route_admin_mapper.detail(route)

    @delete(
        "/{route_id:uuid}/stops/{stop_id:uuid}/dependencies/{depends_on_stop_id:uuid}",
        summary="Remove dependency",
        description="Remove a dependency edge between two stops of the route.",
        status_code=HTTP_200_OK,
    )
    async def remove_dependency(
        self,
        route_id: FromPath[UUID],
        stop_id: FromPath[UUID],
        depends_on_stop_id: FromPath[UUID],
        route_admin_service: NamedDependency[RouteAdminService],
        route_admin_mapper: NamedDependency[RouteAdminMapper],
    ) -> AdminRouteOut:
        route = await route_admin_service.remove_dependency(route_id, stop_id, depends_on_stop_id)
        return await route_admin_mapper.detail(route)
