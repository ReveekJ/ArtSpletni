from dataclasses import dataclass
from typing import TypedDict, cast

from litestar import Litestar
from litestar.testing import AsyncTestClient

Client = AsyncTestClient[Litestar]
Json = dict[str, object]


class PointCardBody(TypedDict):
    id: str
    kind: str
    title: str
    coverUrl: str | None


class RunBody(TypedDict):
    runId: str
    routeId: str
    routeSlug: str
    status: str
    visitedCount: int
    requiredCount: int


class CandidateBody(TypedDict):
    routeId: str
    routeSlug: str
    routeTitle: str
    action: str


class NextStopBody(TypedDict):
    pointId: str | None
    title: str | None
    hint: str | None


class NotificationBody(TypedDict):
    kind: str
    id: str
    title: str | None


class ScanBody(TypedDict):
    outcome: str
    point: PointCardBody | None
    contentAvailable: bool
    run: RunBody | None
    candidates: list[CandidateBody]
    nextStops: list[NextStopBody]
    notifications: list[NotificationBody]


class StopPointBody(TypedDict):
    id: str
    kind: str


class StopBody(TypedDict):
    id: str
    point: StopPointBody
    position: int
    isStart: bool
    dependsOn: list[str]


class IssueBody(TypedDict):
    code: str
    stopId: str | None


class RouteBody(TypedDict):
    id: str
    slug: str
    stops: list[StopBody]
    issues: list[IssueBody]


@dataclass(frozen=True, slots=True)
class TaggedPoint:
    id: str
    token: str


async def create_point(
    admin: Client,
    title: str,
    *,
    kind: str = "gossip",
    published: bool = True,
    blocks: list[Json] | None = None,
    note: dict[str, str] | None = None,
    partner_id: str | None = None,
) -> str:
    payload: Json = {
        "kind": kind,
        "title": {"ru": title},
        "latitude": 55.75,
        "longitude": 37.61,
        "isPublished": published,
        "blocks": blocks
        if blocks is not None
        else [{"kind": "text", "text": {"ru": f"Сплетня про {title}"}}],
    }
    if note is not None:
        payload["note"] = note
    if partner_id is not None:
        payload["partnerId"] = partner_id
    response = await admin.post("/api/admin/points", json=payload)
    assert response.status_code == 201, response.text
    point_id: str = response.json()["id"]
    return point_id


async def issue_tag(admin: Client, point_id: str) -> str:
    response = await admin.post(f"/api/admin/points/{point_id}/tags", json={"label": "main"})
    assert response.status_code == 201, response.text
    url: str = response.json()["url"]
    return url.rsplit("/", 1)[-1]


async def tagged_point(admin: Client, title: str) -> TaggedPoint:
    point_id = await create_point(admin, title)
    return TaggedPoint(id=point_id, token=await issue_tag(admin, point_id))


async def create_route(
    admin: Client,
    slug: str,
    stops: list[tuple[TaggedPoint, bool, bool]],
    *,
    mode: str = "free",
    visibility: str = "all",
    repeatable: bool = False,
    publish: bool = True,
) -> RouteBody:
    response = await admin.post(
        "/api/admin/routes",
        json={
            "slug": slug,
            "title": {"ru": f"Маршрут {slug}"},
            "orderingMode": mode,
            "mapVisibility": visibility,
            "isRepeatable": repeatable,
        },
    )
    assert response.status_code == 201, response.text
    route = cast(RouteBody, response.json())
    for point, is_start, is_required in stops:
        added = await admin.post(
            f"/api/admin/routes/{route['id']}/stops",
            json={
                "pointId": point.id,
                "isStart": is_start,
                "isRequired": is_required,
                "hint": {"ru": "ищи у фонтана"},
            },
        )
        assert added.status_code == 201, added.text
        route = cast(RouteBody, added.json())
    if publish:
        published = await admin.post(f"/api/admin/routes/{route['id']}/publish")
        assert published.status_code == 200, published.text
        route = cast(RouteBody, published.json())
    return route


def stop_id(route: RouteBody, point: TaggedPoint) -> str:
    for stop in route["stops"]:
        if stop["point"]["id"] == point.id:
            return stop["id"]
    raise AssertionError("stop not found")


async def scan(client: Client, point: TaggedPoint) -> ScanBody:
    response = await client.post("/api/scans", json={"token": point.token})
    assert response.status_code == 200, response.text
    return cast(ScanBody, response.json())
