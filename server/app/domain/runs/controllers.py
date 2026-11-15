from uuid import UUID

from litestar import Controller, get, post
from litestar.di import NamedDependency, Provide
from litestar.params import FromPath, JSONBody
from litestar.status_codes import HTTP_200_OK

from app.domain.auth.guards import requires_actor
from app.domain.runs.catalog import RouteCatalogService
from app.domain.runs.deps import (
    provide_progress_bus,
    provide_progress_listeners,
    provide_route_catalog_service,
    provide_run_presenter,
    provide_run_service,
    provide_scan_service,
)
from app.domain.runs.schemas import (
    EngageResponse,
    RouteMapOut,
    RouteSummaryOut,
    RunPresenter,
    RunStateOut,
    StartRunInput,
)
from app.domain.runs.services import RunService
from app.domain.scans.services import ScanService
from app.lib.exceptions import ConflictError
from app.lib.request import AppRequest, require_user

COMMON_DEPENDENCIES = {
    "run_presenter": Provide(provide_run_presenter),
    "route_catalog_service": Provide(provide_route_catalog_service),
}


class RouteController(Controller):
    path = "/api/routes"
    tags = ["Routes"]
    dependencies = COMMON_DEPENDENCIES

    @get("/", summary="List routes", description="Published routes available now, with the user's progress.")
    async def list_routes(
        self, request: AppRequest, route_catalog_service: NamedDependency[RouteCatalogService]
    ) -> list[RouteSummaryOut]:
        return await route_catalog_service.list_all(request.user)

    @get(
        "/{slug:str}",
        summary="Route map",
        description="Route stops filtered by the route's map visibility and the user's progress.",
    )
    async def route_map(
        self,
        request: AppRequest,
        slug: FromPath[str],
        route_catalog_service: NamedDependency[RouteCatalogService],
    ) -> RouteMapOut:
        return await route_catalog_service.route_map(slug, request.user)


class RunController(Controller):
    path = "/api/runs"
    tags = ["Runs"]
    guards = [requires_actor]
    dependencies = {
        **COMMON_DEPENDENCIES,
        "progress_listeners": Provide(provide_progress_listeners),
        "progress_bus": Provide(provide_progress_bus),
        "run_service": Provide(provide_run_service),
        "scan_service": Provide(provide_scan_service),
    }

    @get("/", summary="My runs", description="All route runs of the current user.")
    async def my_runs(
        self, request: AppRequest, route_catalog_service: NamedDependency[RouteCatalogService]
    ) -> list[RunStateOut]:
        return await route_catalog_service.my_runs(require_user(request))

    @post(
        "/",
        summary="Start or resume route",
        description="Start or resume a route from an unlocked point; the current active run is paused.",
        status_code=HTTP_200_OK,
    )
    async def engage(
        self,
        request: AppRequest,
        data: JSONBody[StartRunInput],
        scan_service: NamedDependency[ScanService],
        run_presenter: NamedDependency[RunPresenter],
    ) -> EngageResponse:
        route, change, notifications = await scan_service.engage(
            require_user(request), data.route_id, data.point_id
        )
        if change.run is None:
            raise ConflictError("Route could not be started", code="run_not_started")
        return EngageResponse(run=run_presenter.run_state(route, change.run), notifications=notifications)

    @post(
        "/{run_id:uuid}/abandon",
        summary="Abandon run",
        description="Give up an active or paused run.",
        status_code=HTTP_200_OK,
    )
    async def abandon(
        self,
        request: AppRequest,
        run_id: FromPath[UUID],
        run_service: NamedDependency[RunService],
    ) -> None:
        await run_service.abandon(require_user(request).id, run_id)
