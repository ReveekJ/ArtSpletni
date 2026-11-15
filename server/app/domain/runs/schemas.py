from datetime import datetime
from enum import StrEnum
from uuid import UUID

from app.db.models import MapVisibility, OrderingMode, PointKind, Route, RouteRun, RunStatus, ScanOutcome
from app.domain.points.schemas import PointCard
from app.domain.runs.events import Notification
from app.domain.runs.services import CandidateAction, RouteCandidate
from app.lib.i18n import resolve_text
from app.lib.schema import CamelizedBaseStruct


class RunStateOut(CamelizedBaseStruct):
    run_id: UUID
    route_id: UUID
    route_slug: str
    route_title: str
    status: RunStatus
    visited_count: int
    required_count: int
    required_visited: int
    total_count: int
    started_at: datetime
    completed_at: datetime | None


class CandidateOut(CamelizedBaseStruct):
    route_id: UUID
    route_slug: str
    route_title: str
    action: CandidateAction


class NextStopOut(CamelizedBaseStruct):
    point_id: UUID | None
    title: str | None
    hint: str | None


class ScanResponse(CamelizedBaseStruct):
    outcome: ScanOutcome
    point: PointCard | None
    content_available: bool
    run: RunStateOut | None
    candidates: list[CandidateOut]
    next_stops: list[NextStopOut]
    notifications: list[Notification]


class StartRunInput(CamelizedBaseStruct):
    route_id: UUID
    point_id: UUID


class EngageResponse(CamelizedBaseStruct):
    run: RunStateOut
    notifications: list[Notification]


class StopState(StrEnum):
    VISITED = "visited"
    AVAILABLE = "available"
    LOCKED = "locked"


class MapStopOut(CamelizedBaseStruct):
    stop_id: UUID
    position: int
    state: StopState
    is_start: bool
    is_required: bool
    point_id: UUID | None
    kind: PointKind | None
    title: str | None
    latitude: float | None
    longitude: float | None
    hint: str | None


class RouteSummaryOut(CamelizedBaseStruct):
    id: UUID
    slug: str
    title: str
    description: str | None
    cover_url: str | None
    ordering_mode: OrderingMode
    map_visibility: MapVisibility
    stop_count: int
    active_until: datetime | None
    run: RunStateOut | None


class RouteMapOut(CamelizedBaseStruct):
    route: RouteSummaryOut
    stops: list[MapStopOut]


class RunPresenter:
    def __init__(self, language: str, fallback: str) -> None:
        self.language = language
        self.fallback = fallback

    def title(self, route: Route) -> str:
        return resolve_text(route.title, self.language, self.fallback) or route.slug

    def run_state(self, route: Route, run: RouteRun) -> RunStateOut:
        visited = run.visited_stop_ids
        required = [stop for stop in route.stops if stop.is_required]
        return RunStateOut(
            run_id=run.id,
            route_id=route.id,
            route_slug=route.slug,
            route_title=self.title(route),
            status=run.status,
            visited_count=len(visited),
            required_count=len(required),
            required_visited=sum(1 for stop in required if stop.id in visited),
            total_count=len(route.stops),
            started_at=run.created_at,
            completed_at=run.completed_at,
        )

    def candidate(self, candidate: RouteCandidate) -> CandidateOut:
        return CandidateOut(
            route_id=candidate.route.id,
            route_slug=candidate.route.slug,
            route_title=self.title(candidate.route),
            action=candidate.action,
        )
