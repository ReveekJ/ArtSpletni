import pytest

from tests.conftest import PLAYER_PASSWORD
from tests.helpers import Client, create_route, issue_tag, scan, tagged_point

pytestmark = pytest.mark.runs


async def test_invalid_token_creates_no_session(admin_client: Client, player: Client) -> None:
    body = (await player.post("/api/scans", json={"token": "x" * 43})).json()
    assert body["outcome"] == "invalid_tag"
    assert (await player.get("/api/auth/session")).json() == {"user": None}


async def test_standalone_point_unlocks_for_guest(
    admin_client: Client, player: Client, other_player: Client
) -> None:
    point = await tagged_point(admin_client, "Аптека")

    body = await scan(player, point)

    assert body["outcome"] == "unlocked"
    assert body["contentAvailable"] is True
    assert body["point"] is not None
    assert body["point"]["title"] == "Аптека"
    session = (await player.get("/api/auth/session")).json()
    assert session["user"]["kind"] == "guest"
    content = await player.get(f"/api/points/{point.id}")
    assert content.status_code == 200
    assert content.json()["blocks"][0]["text"] == "Сплетня про Аптека"
    assert (await other_player.get(f"/api/points/{point.id}")).status_code == 401
    collection = (await player.get("/api/me/collection")).json()
    assert [item["point"]["id"] for item in collection] == [point.id]


async def test_content_requires_own_unlock(admin_client: Client, player: Client) -> None:
    point = await tagged_point(admin_client, "Секрет")
    await player.post("/api/auth/register", json={"email": "p@example.com", "password": PLAYER_PASSWORD})

    response = await player.get(f"/api/points/{point.id}")

    assert response.status_code == 403
    assert response.json()["code"] == "point_locked"


async def test_revoked_tag_and_unpublished_point(admin_client: Client, player: Client) -> None:
    point = await tagged_point(admin_client, "Старая метка")
    tags = (await admin_client.get(f"/api/admin/points/{point.id}/tags")).json()
    await admin_client.post(f"/api/admin/tags/{tags[0]['id']}/revoke")
    assert (await scan(player, point))["outcome"] == "invalid_tag"

    point_id = (
        await admin_client.post(
            "/api/admin/points",
            json={
                "kind": "gossip",
                "title": {"ru": "Черновик"},
                "latitude": 1,
                "longitude": 1,
                "blocks": [{"kind": "text", "text": {"ru": "т"}}],
            },
        )
    ).json()["id"]
    token = await issue_tag(admin_client, point_id)
    body = (await player.post("/api/scans", json={"token": token})).json()
    assert body["outcome"] == "point_unavailable"


async def test_free_route_start_rules_and_completion(admin_client: Client, player: Client) -> None:
    a = await tagged_point(admin_client, "A")
    b = await tagged_point(admin_client, "B")
    await create_route(admin_client, "free", [(a, True, True), (b, False, True)])

    not_start = await scan(player, b)
    assert not_start["outcome"] == "not_a_start"
    assert not_start["contentAvailable"] is False

    started = await scan(player, a)
    assert started["outcome"] == "route_started"
    assert started["run"] is not None
    assert started["run"]["visitedCount"] == 1

    finished = await scan(player, b)
    assert finished["outcome"] == "route_completed"
    assert finished["run"] is not None
    assert finished["run"]["status"] == "completed"

    again = await scan(player, a)
    assert again["outcome"] == "unlocked"
    runs = (await player.get("/api/runs")).json()
    assert len(runs) == 1


async def test_sequential_route_locks_out_of_order(admin_client: Client, player: Client) -> None:
    a, b, c = [await tagged_point(admin_client, name) for name in ("A", "B", "C")]
    await create_route(
        admin_client, "seq", [(a, True, True), (b, False, True), (c, False, True)], mode="sequential"
    )

    await scan(player, a)
    locked = await scan(player, c)

    assert locked["outcome"] == "locked"
    assert locked["contentAvailable"] is False
    assert [stop["pointId"] for stop in locked["nextStops"]] == [b.id]
    assert (await scan(player, b))["outcome"] == "visited"
    assert (await scan(player, c))["outcome"] == "route_completed"


async def test_graph_route_dependencies(admin_client: Client, player: Client) -> None:
    a, b, c = [await tagged_point(admin_client, name) for name in ("A", "B", "C")]
    route = await create_route(
        admin_client,
        "graph",
        [(a, True, True), (b, False, True), (c, False, True)],
        mode="graph",
        publish=False,
    )
    stops = {stop["point"]["id"]: stop["id"] for stop in route["stops"]}
    for dependency in (a, b):
        response = await admin_client.post(
            f"/api/admin/routes/{route['id']}/stops/{stops[c.id]}/dependencies",
            json={"dependsOnStopId": stops[dependency.id]},
        )
        assert response.status_code == 201
    assert (await admin_client.post(f"/api/admin/routes/{route['id']}/publish")).status_code == 200

    await scan(player, a)
    assert (await scan(player, c))["outcome"] == "locked"
    await scan(player, b)
    assert (await scan(player, c))["outcome"] == "route_completed"


async def test_switch_and_resume_routes(admin_client: Client, player: Client) -> None:
    a, a2, x, x2 = [await tagged_point(admin_client, name) for name in ("A", "A2", "X", "X2")]
    first = await create_route(admin_client, "first", [(a, True, True), (a2, False, True)])
    second = await create_route(admin_client, "second", [(x, True, True), (x2, False, True)])

    await scan(player, a)
    offer = await scan(player, x)
    assert offer["outcome"] == "switch_offer"
    assert offer["contentAvailable"] is True
    assert offer["candidates"] == [
        {"routeId": second["id"], "routeSlug": "second", "routeTitle": "Маршрут second", "action": "start"}
    ]

    switched = await player.post("/api/runs", json={"routeId": second["id"], "pointId": x.id})
    assert switched.status_code == 200
    assert switched.json()["run"]["visitedCount"] == 1

    statuses = {run["routeSlug"]: run["status"] for run in (await player.get("/api/runs")).json()}
    assert statuses == {"first": "paused", "second": "active"}

    resume = await scan(player, a2)
    assert resume["outcome"] == "switch_offer"
    assert resume["candidates"][0]["action"] == "resume"
    resumed = await player.post("/api/runs", json={"routeId": first["id"], "pointId": a2.id})
    assert resumed.json()["run"]["status"] == "completed"


async def test_choose_between_routes_sharing_start(admin_client: Client, player: Client) -> None:
    hub, left, right = [await tagged_point(admin_client, name) for name in ("Hub", "L", "R")]
    left_route = await create_route(admin_client, "left", [(hub, True, True), (left, False, True)])
    await create_route(admin_client, "right", [(hub, True, True), (right, False, True)])

    choice = await scan(player, hub)
    assert choice["outcome"] == "choose_route"
    assert {candidate["routeSlug"] for candidate in choice["candidates"]} == {"left", "right"}

    started = await player.post("/api/runs", json={"routeId": left_route["id"], "pointId": hub.id})
    assert started.json()["run"]["routeSlug"] == "left"


async def test_cannot_start_route_without_unlock(admin_client: Client, player: Client) -> None:
    a = await tagged_point(admin_client, "A")
    route = await create_route(admin_client, "locked", [(a, True, True)])
    await player.post("/api/auth/register", json={"email": "nope@example.com", "password": PLAYER_PASSWORD})

    response = await player.post("/api/runs", json={"routeId": route["id"], "pointId": a.id})

    assert response.status_code == 403
    assert response.json()["code"] == "point_locked"


async def test_repeatable_route_can_restart(admin_client: Client, player: Client) -> None:
    a = await tagged_point(admin_client, "A")
    await create_route(admin_client, "loop", [(a, True, True)], repeatable=True)

    assert (await scan(player, a))["outcome"] == "route_completed"
    assert (await scan(player, a))["outcome"] == "route_completed"
    assert len((await player.get("/api/runs")).json()) == 2


async def test_guest_progress_merges_into_account(
    admin_client: Client, player: Client, other_player: Client
) -> None:
    a, b = await tagged_point(admin_client, "A"), await tagged_point(admin_client, "B")
    await create_route(admin_client, "merge", [(a, True, True), (b, False, True)])
    await other_player.post(
        "/api/auth/register", json={"email": "owner@example.com", "password": PLAYER_PASSWORD}
    )

    await scan(player, a)
    login = await player.post(
        "/api/auth/login", json={"email": "owner@example.com", "password": PLAYER_PASSWORD}
    )
    assert login.status_code == 200

    collection = (await player.get("/api/me/collection")).json()
    assert [item["point"]["id"] for item in collection] == [a.id]
    runs = (await player.get("/api/runs")).json()
    assert [(run["routeSlug"], run["status"]) for run in runs] == [("merge", "active")]
    assert (await scan(player, b))["outcome"] == "route_completed"


async def test_guest_registration_keeps_progress(admin_client: Client, player: Client) -> None:
    a = await tagged_point(admin_client, "A")
    await scan(player, a)

    response = await player.post(
        "/api/auth/register", json={"email": "new@example.com", "password": PLAYER_PASSWORD}
    )

    assert response.json()["kind"] == "registered"
    assert len((await player.get("/api/me/collection")).json()) == 1
