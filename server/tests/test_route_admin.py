import pytest

from tests.helpers import Client, create_route, scan, stop_id, tagged_point

pytestmark = pytest.mark.routes


async def test_publish_requires_valid_route(admin_client: Client) -> None:
    a = await tagged_point(admin_client, "A")
    route = await create_route(admin_client, "draft", [(a, False, True)], publish=False)
    assert [issue["code"] for issue in route["issues"]] == ["no_start"]

    response = await admin_client.post(f"/api/admin/routes/{route['id']}/publish")
    assert response.status_code == 409
    assert response.json()["code"] == "route_invalid"


async def test_published_route_rejects_breaking_edits(admin_client: Client) -> None:
    a = await tagged_point(admin_client, "A")
    route = await create_route(admin_client, "live", [(a, True, True)])

    response = await admin_client.patch(
        f"/api/admin/routes/{route['id']}/stops/{stop_id(route, a)}", json={"isStart": False}
    )

    assert response.status_code == 409
    current = (await admin_client.get(f"/api/admin/routes/{route['id']}")).json()
    assert current["stops"][0]["isStart"] is True


async def test_dependency_rules(admin_client: Client) -> None:
    a, b = await tagged_point(admin_client, "A"), await tagged_point(admin_client, "B")
    free = await create_route(admin_client, "free", [(a, True, True), (b, False, True)], publish=False)
    not_graph = await admin_client.post(
        f"/api/admin/routes/{free['id']}/stops/{stop_id(free, b)}/dependencies",
        json={"dependsOnStopId": stop_id(free, a)},
    )
    assert not_graph.json()["code"] == "not_graph_mode"

    graph = await create_route(
        admin_client, "graph", [(a, True, True), (b, False, True)], mode="graph", publish=False
    )
    base = f"/api/admin/routes/{graph['id']}/stops"
    a_stop, b_stop = stop_id(graph, a), stop_id(graph, b)
    assert (
        await admin_client.post(f"{base}/{b_stop}/dependencies", json={"dependsOnStopId": a_stop})
    ).status_code == 201
    cycle = await admin_client.post(f"{base}/{a_stop}/dependencies", json={"dependsOnStopId": b_stop})
    assert cycle.status_code == 409
    assert cycle.json()["code"] == "dependency_cycle"

    removed = await admin_client.delete(f"{base}/{b_stop}/dependencies/{a_stop}")
    assert removed.json()["stops"][1]["dependsOn"] == []


async def test_reorder_and_remove_stop(admin_client: Client) -> None:
    a, b, c = [await tagged_point(admin_client, name) for name in ("A", "B", "C")]
    route = await create_route(
        admin_client, "order", [(a, True, True), (b, False, True), (c, False, True)], publish=False
    )
    ids = [stop_id(route, point) for point in (c, a, b)]

    reordered = (
        await admin_client.put(f"/api/admin/routes/{route['id']}/stops/order", json={"stopIds": ids})
    ).json()
    assert [stop["point"]["id"] for stop in reordered["stops"]] == [c.id, a.id, b.id]

    bad = await admin_client.put(f"/api/admin/routes/{route['id']}/stops/order", json={"stopIds": ids[:2]})
    assert bad.json()["code"] == "invalid_order"

    removed = (await admin_client.delete(f"/api/admin/routes/{route['id']}/stops/{ids[0]}")).json()
    assert [stop["position"] for stop in removed["stops"]] == [0, 1]


async def test_point_in_route_cannot_be_deleted(admin_client: Client) -> None:
    a = await tagged_point(admin_client, "A")
    await create_route(admin_client, "keep", [(a, True, True)], publish=False)

    response = await admin_client.delete(f"/api/admin/points/{a.id}")

    assert response.json()["code"] == "point_in_route"


async def test_route_with_progress_cannot_be_deleted(admin_client: Client, player: Client) -> None:
    a = await tagged_point(admin_client, "A")
    route = await create_route(admin_client, "used", [(a, True, True)])
    await scan(player, a)

    response = await admin_client.delete(f"/api/admin/routes/{route['id']}")

    assert response.json()["code"] == "route_has_runs"


async def test_progressive_map_hides_locked_stops(admin_client: Client, player: Client) -> None:
    a, b = await tagged_point(admin_client, "A"), await tagged_point(admin_client, "B")
    await create_route(
        admin_client,
        "fog",
        [(a, True, True), (b, False, True)],
        mode="sequential",
        visibility="visited_with_hints",
    )

    before = (await player.get("/api/routes/fog")).json()
    assert [(stop["state"], stop["pointId"], stop["hint"]) for stop in before["stops"]] == [
        ("available", None, "ищи у фонтана"),
        ("locked", None, None),
    ]

    await scan(player, a)
    after = (await player.get("/api/routes/fog")).json()
    assert after["stops"][0]["state"] == "visited"
    assert after["stops"][0]["pointId"] == a.id
    assert after["stops"][1]["state"] == "available"
    assert after["stops"][1]["latitude"] is None
    assert after["route"]["run"]["status"] == "active"


async def test_route_list_shows_only_published(admin_client: Client, player: Client) -> None:
    a = await tagged_point(admin_client, "A")
    await create_route(admin_client, "visible", [(a, True, True)])
    await create_route(admin_client, "hidden", [(a, True, True)], publish=False)

    slugs = [route["slug"] for route in (await player.get("/api/routes")).json()]

    assert slugs == ["visible"]
    assert (await player.get("/api/routes/hidden")).status_code == 404


async def test_point_validation(admin_client: Client) -> None:
    empty = await admin_client.post(
        "/api/admin/points",
        json={"kind": "gossip", "title": {"ru": "Пусто"}, "latitude": 1, "longitude": 1, "blocks": []},
    )
    assert empty.json()["code"] == "content_required"

    no_partner = await admin_client.post(
        "/api/admin/points",
        json={"kind": "partner", "title": {"ru": "Кафе"}, "latitude": 1, "longitude": 1, "blocks": []},
    )
    assert no_partner.json()["code"] == "partner_required"

    missing_media = await admin_client.post(
        "/api/admin/points",
        json={
            "kind": "gossip",
            "title": {"ru": "Аудио"},
            "latitude": 1,
            "longitude": 1,
            "blocks": [{"kind": "audio"}],
        },
    )
    assert missing_media.json()["code"] == "invalid_block"
