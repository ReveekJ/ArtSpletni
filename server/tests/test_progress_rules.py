from uuid import UUID, uuid4

import pytest

from app.db.models import OrderingMode
from app.domain.routes.progress import IssueCode, StopNode, available_stops, is_completed, validate

pytestmark = pytest.mark.routes


def node(
    position: int, *, start: bool = False, required: bool = True, deps: frozenset[UUID] = frozenset()
) -> StopNode:
    return StopNode(id=uuid4(), position=position, is_start=start, is_required=required, depends_on=deps)


def test_free_mode_opens_everything_after_start() -> None:
    a, b, c = node(0, start=True), node(1), node(2)
    stops = [a, b, c]
    assert available_stops(OrderingMode.FREE, stops, []) == {a.id}
    assert available_stops(OrderingMode.FREE, stops, [a.id]) == {b.id, c.id}


def test_sequential_mode_wraps_and_skips_optional() -> None:
    a, b, c, d = node(0, start=True), node(1, required=False), node(2), node(3, start=True)
    stops = [a, b, c, d]
    assert available_stops(OrderingMode.SEQUENTIAL, stops, []) == {a.id, d.id}
    assert available_stops(OrderingMode.SEQUENTIAL, stops, [a.id]) == {b.id, c.id}
    assert available_stops(OrderingMode.SEQUENTIAL, stops, [d.id]) == {a.id}
    assert available_stops(OrderingMode.SEQUENTIAL, stops, [d.id, a.id, c.id]) == {b.id}
    assert is_completed(stops, [d.id, a.id, c.id])


def test_graph_mode_requires_all_dependencies() -> None:
    a, b = node(0, start=True), node(1)
    c = node(2, deps=frozenset({a.id, b.id}))
    stops = [a, b, c]
    assert available_stops(OrderingMode.GRAPH, stops, [a.id]) == {b.id}
    assert available_stops(OrderingMode.GRAPH, stops, [a.id, b.id]) == {c.id}


def test_validation_reports_structural_issues() -> None:
    assert [issue.code for issue in validate(OrderingMode.FREE, [])] == [IssueCode.NO_STOPS]
    assert IssueCode.NO_START in {issue.code for issue in validate(OrderingMode.FREE, [node(0)])}

    a, b = node(0, start=True), node(1)
    cyclic = [a, StopNode(b.id, 1, False, True, frozenset({b.id}))]
    assert IssueCode.CYCLE in {issue.code for issue in validate(OrderingMode.GRAPH, cyclic)}

    start_with_dep = [node(0, start=True, deps=frozenset({uuid4()}))]
    assert IssueCode.START_HAS_DEPENDENCIES in {
        issue.code for issue in validate(OrderingMode.GRAPH, start_with_dep)
    }


def test_validation_detects_unreachable_required_stop() -> None:
    a = node(0, start=True)
    ghost = uuid4()
    orphan = node(1, deps=frozenset({ghost}))
    issues = validate(OrderingMode.GRAPH, [a, orphan])
    assert [(issue.code, issue.stop_id) for issue in issues] == [(IssueCode.UNREACHABLE, orphan.id)]
    assert validate(OrderingMode.GRAPH, [a, node(1, deps=frozenset({a.id}))]) == []
