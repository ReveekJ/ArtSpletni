from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from app.db.models import Route, RouteRun, RouteStop, RunStatus, StopVisit
from app.domain.points.repositories import UnlockRepository
from app.domain.routes import progress
from app.domain.runs.events import PointUnlocked, ProgressEvent, RouteCompleted, StopVisited
from app.domain.runs.repositories import RunRepository
from app.lib.exceptions import ConflictError


class CandidateAction(StrEnum):
    START = "start"
    RESUME = "resume"


@dataclass(frozen=True, slots=True)
class RouteCandidate:
    route: Route
    stop: RouteStop
    action: CandidateAction
    run: RouteRun | None = None


@dataclass(slots=True)
class ProgressChange:
    run: RouteRun | None = None
    events: list[ProgressEvent] = field(default_factory=list)
    completed: bool = False


def stop_for_point(route: Route, point_id: UUID) -> RouteStop | None:
    return next((stop for stop in route.stops if stop.point_id == point_id), None)


def visit_order(run: RouteRun) -> list[UUID]:
    return [visit.stop_id for visit in sorted(run.visits, key=lambda item: item.created_at)]


def available_in_run(route: Route, run: RouteRun | None) -> set[UUID]:
    visited = visit_order(run) if run is not None else []
    return progress.available_stops(route.ordering_mode, progress.nodes_of(route), visited)


class RunService:
    def __init__(self, runs: RunRepository, unlocks: UnlockRepository) -> None:
        self._runs = runs
        self._unlocks = unlocks

    async def active(self, user_id: UUID) -> RouteRun | None:
        return await self._runs.active_for_user(user_id)

    async def unlock(self, user_id: UUID, point_id: UUID, at: datetime) -> list[ProgressEvent]:
        created = await self._unlocks.ensure(user_id, point_id)
        return [PointUnlocked(user_id=user_id, point_id=point_id, at=at)] if created else []

    async def candidate(self, user_id: UUID, route: Route, point_id: UUID) -> RouteCandidate | None:
        stop = stop_for_point(route, point_id)
        if stop is None:
            return None
        runs = await self._runs.for_user_route(user_id, route.id)
        if any(run.status is RunStatus.ACTIVE for run in runs):
            return None
        paused = next((run for run in runs if run.status is RunStatus.PAUSED), None)
        if paused is not None:
            reachable = stop.id in paused.visited_stop_ids or stop.id in available_in_run(route, paused)
            return RouteCandidate(route, stop, CandidateAction.RESUME, paused) if reachable else None
        if not stop.is_start or stop.id not in available_in_run(route, None):
            return None
        completed = any(run.status is RunStatus.COMPLETED for run in runs)
        if completed and not route.is_repeatable:
            return None
        return RouteCandidate(route, stop, CandidateAction.START)

    async def engage(self, user_id: UUID, candidate: RouteCandidate, at: datetime) -> ProgressChange:
        current = await self._runs.active_for_user(user_id)
        if current is not None:
            current.status = RunStatus.PAUSED
            await self._runs.update(current, auto_refresh=False)
        if candidate.action is CandidateAction.RESUME:
            if candidate.run is None:
                raise ConflictError("Nothing to resume", code="run_not_found")
            run = candidate.run
            run.status = RunStatus.ACTIVE
            run = await self._runs.update(run, auto_refresh=False)
        else:
            run = await self._runs.add(RouteRun(user_id=user_id, route_id=candidate.route.id, visits=[]))
        if candidate.stop.id in run.visited_stop_ids:
            return ProgressChange(run=run)
        return await self.visit(user_id, run, candidate.route, candidate.stop, at)

    async def visit(
        self, user_id: UUID, run: RouteRun, route: Route, stop: RouteStop, at: datetime
    ) -> ProgressChange:
        run.visits.append(StopVisit(stop_id=stop.id, created_at=at))
        change = ProgressChange(
            run=run,
            events=[
                StopVisited(
                    user_id=user_id,
                    run_id=run.id,
                    route_id=route.id,
                    stop_id=stop.id,
                    point_id=stop.point_id,
                    at=at,
                )
            ],
        )
        nodes = progress.nodes_of(route)
        visited = visit_order(run)
        if progress.is_completed(nodes, visited):
            run.status = RunStatus.COMPLETED
            run.completed_at = at
            change.completed = True
            change.events.append(
                RouteCompleted(
                    user_id=user_id,
                    run_id=run.id,
                    route_id=route.id,
                    started_at=run.created_at,
                    at=at,
                    fully=progress.is_fully_completed(nodes, visited),
                )
            )
        change.run = await self._runs.update(run, auto_refresh=False)
        return change

    async def abandon(self, user_id: UUID, run_id: UUID) -> RouteRun:
        run = await self._runs.get_one_or_none(id=run_id, user_id=user_id)
        if run is None or run.status is RunStatus.COMPLETED:
            raise ConflictError("Run cannot be abandoned", code="run_not_abandonable")
        run.status = RunStatus.ABANDONED
        return await self._runs.update(run, auto_refresh=False)


def utcnow() -> datetime:
    return datetime.now(UTC)
