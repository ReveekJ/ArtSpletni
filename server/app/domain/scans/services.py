from dataclasses import dataclass, field
from uuid import UUID

from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from app.db.models import MapVisibility, Point, Route, RouteRun, RouteStop, ScanEvent, ScanOutcome, User
from app.domain.nfc.services import NfcTagService
from app.domain.points.repositories import PointRepository, UnlockRepository
from app.domain.routes.repositories import RouteRepository
from app.domain.runs.events import Notification, ProgressEventBus
from app.domain.runs.services import (
    CandidateAction,
    ProgressChange,
    RouteCandidate,
    RunService,
    available_in_run,
    stop_for_point,
    utcnow,
)
from app.domain.users.services import UserService
from app.lib.exceptions import ForbiddenError, NotFoundError


class ScanEventRepository(SQLAlchemyAsyncRepository[ScanEvent]):
    model_type = ScanEvent


@dataclass(slots=True)
class NextStop:
    point: Point | None
    stop: RouteStop
    show_point: bool


@dataclass(slots=True)
class ScanResult:
    outcome: ScanOutcome
    user: User | None = None
    point: Point | None = None
    content_available: bool = False
    route: Route | None = None
    run: RouteRun | None = None
    candidates: list[RouteCandidate] = field(default_factory=list)
    next_stops: list[NextStop] = field(default_factory=list)
    notifications: list[Notification] = field(default_factory=list)


class ScanService:
    def __init__(
        self,
        tags: NfcTagService,
        users: UserService,
        points: PointRepository,
        unlocks: UnlockRepository,
        routes: RouteRepository,
        runs: RunService,
        scan_events: ScanEventRepository,
        bus: ProgressEventBus,
    ) -> None:
        self._tags = tags
        self._users = users
        self._points = points
        self._unlocks = unlocks
        self._routes = routes
        self._runs = runs
        self._events = scan_events
        self._bus = bus

    async def scan(self, token: str, actor: User | None) -> ScanResult:
        tag = await self._tags.resolve(token)
        if tag is None:
            await self._log(ScanOutcome.INVALID_TAG, actor, None, None, None)
            return ScanResult(outcome=ScanOutcome.INVALID_TAG, user=actor)
        point = await self._points.get_one_or_none(id=tag.point_id)
        if point is None or not point.is_published:
            await self._log(ScanOutcome.POINT_UNAVAILABLE, actor, tag.id, tag.point_id, None)
            return ScanResult(outcome=ScanOutcome.POINT_UNAVAILABLE, user=actor)
        user = actor if actor is not None else await self._users.create_guest()
        result = await self._resolve(user, point)
        result.user = user
        result.point = point
        result.content_available = (
            await self._unlocks.get_one_or_none(user_id=user.id, point_id=point.id) is not None
        )
        await self._log(result.outcome, user, tag.id, point.id, result.route.id if result.route else None)
        return result

    async def engage(
        self, user: User, route_id: UUID, point_id: UUID
    ) -> tuple[Route, ProgressChange, list[Notification]]:
        if await self._unlocks.get_one_or_none(user_id=user.id, point_id=point_id) is None:
            raise ForbiddenError("Scan the point before starting a route from it", code="point_locked")
        route = next(
            (
                item
                for item in await self._routes.published_with_point(point_id, utcnow())
                if item.id == route_id
            ),
            None,
        )
        if route is None:
            raise NotFoundError("Route is not available from this point", code="route_unavailable")
        candidate = await self._runs.candidate(user.id, route, point_id)
        if candidate is None:
            raise ForbiddenError("This route cannot be started from this point", code="not_a_start")
        change = await self._runs.engage(user.id, candidate, utcnow())
        notifications = await self._bus.publish(change.events)
        return route, change, notifications

    async def _resolve(self, user: User, point: Point) -> ScanResult:
        now = utcnow()
        routes = await self._routes.published_with_point(point.id, now)
        active = await self._runs.active(user.id)
        active_route = next((route for route in routes if active and route.id == active.route_id), None)
        if active is not None and active_route is not None:
            stop = stop_for_point(active_route, point.id)
            if stop is not None:
                return await self._within_run(user, point, active_route, active, stop)
        candidates = [
            candidate
            for route in routes
            if (candidate := await self._runs.candidate(user.id, route, point.id)) is not None
        ]
        if candidates:
            return await self._with_candidates(user, point, active, candidates)
        if routes and await self._unlocks.get_one_or_none(user_id=user.id, point_id=point.id) is None:
            return ScanResult(outcome=ScanOutcome.NOT_A_START, route=routes[0])
        events = await self._runs.unlock(user.id, point.id, now)
        return ScanResult(outcome=ScanOutcome.UNLOCKED, notifications=await self._bus.publish(events))

    async def _within_run(
        self, user: User, point: Point, route: Route, run: RouteRun, stop: RouteStop
    ) -> ScanResult:
        now = utcnow()
        if stop.id in run.visited_stop_ids:
            events = await self._runs.unlock(user.id, point.id, now)
            return ScanResult(
                outcome=ScanOutcome.REVISITED,
                route=route,
                run=run,
                notifications=await self._bus.publish(events),
            )
        if stop.id not in available_in_run(route, run):
            return ScanResult(
                outcome=ScanOutcome.LOCKED,
                route=route,
                run=run,
                next_stops=await self._next_stops(route, available_in_run(route, run)),
            )
        events = await self._runs.unlock(user.id, point.id, now)
        change = await self._runs.visit(user.id, run, route, stop, now)
        return ScanResult(
            outcome=ScanOutcome.ROUTE_COMPLETED if change.completed else ScanOutcome.VISITED,
            route=route,
            run=change.run,
            notifications=await self._bus.publish([*events, *change.events]),
        )

    async def _with_candidates(
        self, user: User, point: Point, active: RouteRun | None, candidates: list[RouteCandidate]
    ) -> ScanResult:
        now = utcnow()
        events = await self._runs.unlock(user.id, point.id, now)
        if active is None and len(candidates) == 1:
            candidate = candidates[0]
            change = await self._runs.engage(user.id, candidate, now)
            outcome = (
                ScanOutcome.VISITED
                if candidate.action is CandidateAction.RESUME
                else ScanOutcome.ROUTE_STARTED
            )
            return ScanResult(
                outcome=ScanOutcome.ROUTE_COMPLETED if change.completed else outcome,
                route=candidate.route,
                run=change.run,
                notifications=await self._bus.publish([*events, *change.events]),
            )
        return ScanResult(
            outcome=ScanOutcome.CHOOSE_ROUTE if active is None else ScanOutcome.SWITCH_OFFER,
            candidates=candidates,
            notifications=await self._bus.publish(events),
        )

    async def _next_stops(self, route: Route, stop_ids: set[UUID]) -> list[NextStop]:
        stops = [stop for stop in route.stops if stop.id in stop_ids]
        points = {
            point.id: point
            for point in await self._points.get_many(Point.id.in_([stop.point_id for stop in stops]))
        }
        show_point = route.map_visibility is not MapVisibility.VISITED_WITH_HINTS
        return [NextStop(point=points.get(stop.point_id), stop=stop, show_point=show_point) for stop in stops]

    async def _log(
        self,
        outcome: ScanOutcome,
        user: User | None,
        tag_id: UUID | None,
        point_id: UUID | None,
        route_id: UUID | None,
    ) -> None:
        await self._events.add(
            ScanEvent(
                outcome=outcome,
                user_id=user.id if user else None,
                tag_id=tag_id,
                point_id=point_id,
                route_id=route_id,
            )
        )
