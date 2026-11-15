from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from app.db.models import OrderingMode, Route


@dataclass(frozen=True, slots=True)
class StopNode:
    id: UUID
    position: int
    is_start: bool
    is_required: bool
    depends_on: frozenset[UUID]


class IssueCode(StrEnum):
    NO_STOPS = "no_stops"
    NO_START = "no_start"
    CYCLE = "cycle"
    START_HAS_DEPENDENCIES = "start_has_dependencies"
    UNREACHABLE = "unreachable"
    NO_REQUIRED = "no_required"


@dataclass(frozen=True, slots=True)
class RouteIssue:
    code: IssueCode
    stop_id: UUID | None = None


def nodes_of(route: Route) -> list[StopNode]:
    use_dependencies = route.ordering_mode is OrderingMode.GRAPH
    return [
        StopNode(
            id=stop.id,
            position=stop.position,
            is_start=stop.is_start,
            is_required=stop.is_required,
            depends_on=frozenset(dep.depends_on_stop_id for dep in stop.dependencies)
            if use_dependencies
            else frozenset(),
        )
        for stop in sorted(route.stops, key=lambda item: item.position)
    ]


def available_stops(mode: OrderingMode, stops: Sequence[StopNode], visited: Sequence[UUID]) -> set[UUID]:
    if not visited:
        return {stop.id for stop in stops if stop.is_start and not stop.depends_on}
    seen = set(visited)
    if mode is OrderingMode.FREE:
        return {stop.id for stop in stops if stop.id not in seen}
    if mode is OrderingMode.GRAPH:
        return {stop.id for stop in stops if stop.id not in seen and stop.depends_on <= seen}
    return _sequential_available(stops, visited[-1], seen)


def _sequential_available(stops: Sequence[StopNode], last: UUID, seen: set[UUID]) -> set[UUID]:
    ordered = sorted(stops, key=lambda stop: stop.position)
    index = next((i for i, stop in enumerate(ordered) if stop.id == last), None)
    if index is None:
        return set()
    result: set[UUID] = set()
    for offset in range(1, len(ordered)):
        stop = ordered[(index + offset) % len(ordered)]
        if stop.id in seen:
            continue
        result.add(stop.id)
        if stop.is_required:
            break
    return result


def is_completed(stops: Sequence[StopNode], visited: Sequence[UUID]) -> bool:
    seen = set(visited)
    return all(stop.id in seen for stop in stops if stop.is_required)


def is_fully_completed(stops: Sequence[StopNode], visited: Sequence[UUID]) -> bool:
    seen = set(visited)
    return all(stop.id in seen for stop in stops)


def validate(mode: OrderingMode, stops: Sequence[StopNode]) -> list[RouteIssue]:
    if not stops:
        return [RouteIssue(IssueCode.NO_STOPS)]
    issues: list[RouteIssue] = []
    if not any(stop.is_start for stop in stops):
        issues.append(RouteIssue(IssueCode.NO_START))
    if not any(stop.is_required for stop in stops):
        issues.append(RouteIssue(IssueCode.NO_REQUIRED))
    if mode is OrderingMode.GRAPH:
        issues.extend(
            RouteIssue(IssueCode.START_HAS_DEPENDENCIES, stop.id)
            for stop in stops
            if stop.is_start and stop.depends_on
        )
        cycle_stop = find_cycle(stops)
        if cycle_stop is not None:
            issues.append(RouteIssue(IssueCode.CYCLE, cycle_stop))
    if issues:
        return issues
    reachable = _reachable(mode, stops)
    return [
        RouteIssue(IssueCode.UNREACHABLE, stop.id)
        for stop in stops
        if stop.is_required and stop.id not in reachable
    ]


def _reachable(mode: OrderingMode, stops: Sequence[StopNode]) -> set[UUID]:
    if mode is not OrderingMode.GRAPH:
        return {stop.id for stop in stops}
    visited: list[UUID] = []
    frontier = available_stops(mode, stops, visited)
    while frontier:
        visited.extend(sorted(frontier))
        frontier = available_stops(mode, stops, visited)
    return set(visited)


def find_cycle(stops: Sequence[StopNode]) -> UUID | None:
    graph = {stop.id: stop.depends_on for stop in stops}
    state: dict[UUID, int] = {}

    def visit(node: UUID) -> UUID | None:
        state[node] = 1
        for dependency in graph.get(node, frozenset()):
            mark = state.get(dependency, 0)
            if mark == 1:
                return dependency
            if mark == 0:
                found = visit(dependency)
                if found is not None:
                    return found
        state[node] = 2
        return None

    for node in graph:
        if state.get(node, 0) == 0:
            found = visit(node)
            if found is not None:
                return found
    return None
