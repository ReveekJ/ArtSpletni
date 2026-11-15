import pytest

from tests.conftest import PLAYER_PASSWORD
from tests.fakes import FakeObjectStorage
from tests.helpers import Client, create_point, create_route, issue_tag, scan, tagged_point

pytestmark = pytest.mark.submissions

STORY = "Говорят, в этом доме жил купец, который прятал золото в печи."


async def _own_upload(client: Client, storage: FakeObjectStorage) -> str:
    ticket = (
        await client.post(
            "/api/me/media/uploads", json={"kind": "image", "contentType": "image/jpeg", "sizeBytes": 50}
        )
    ).json()
    storage.objects[ticket["uploadUrl"].removeprefix("https://storage.test/upload/")] = 50
    completed = await client.post(f"/api/me/media/{ticket['asset']['id']}/complete")
    assert completed.status_code == 200
    asset_id: str = ticket["asset"]["id"]
    return asset_id


async def test_guest_cannot_submit(admin_client: Client, player: Client) -> None:
    await scan(player, await tagged_point(admin_client, "A"))

    response = await player.post(
        "/api/me/submissions", json={"title": "Дом", "story": STORY, "latitude": 55.7, "longitude": 37.6}
    )

    assert response.json()["code"] == "registration_required"


async def test_submission_approval_creates_draft_point(
    admin_client: Client, player: Client, storage: FakeObjectStorage
) -> None:
    await player.post("/api/auth/register", json={"email": "author@example.com", "password": PLAYER_PASSWORD})
    asset_id = await _own_upload(player, storage)

    created = await player.post(
        "/api/me/submissions",
        json={
            "title": "Дом купца",
            "story": STORY,
            "latitude": 55.7,
            "longitude": 37.6,
            "assetIds": [asset_id],
        },
    )
    assert created.status_code == 201, created.text

    pending = (await admin_client.get("/api/admin/submissions")).json()
    assert [(item["submission"]["title"], item["authorEmail"]) for item in pending] == [
        ("Дом купца", "author@example.com")
    ]
    submission_id = pending[0]["submission"]["id"]

    approved = (await admin_client.post(f"/api/admin/submissions/{submission_id}/approve")).json()
    assert approved["status"] == "approved"
    point = (await admin_client.get(f"/api/admin/points/{approved['pointId']}")).json()
    assert point["isPublished"] is False
    assert point["title"]["ru"]["text"] == "Дом купца"
    assert [block["kind"] for block in point["blocks"]] == ["text", "image"]

    again = await admin_client.post(f"/api/admin/submissions/{submission_id}/reject", json={})
    assert again.json()["code"] == "submission_moderated"
    mine = (await player.get("/api/me/submissions")).json()
    assert mine[0]["status"] == "approved"


async def test_foreign_media_and_rejection(
    admin_client: Client, player: Client, other_player: Client, storage: FakeObjectStorage
) -> None:
    await player.post("/api/auth/register", json={"email": "one@example.com", "password": PLAYER_PASSWORD})
    await other_player.post(
        "/api/auth/register", json={"email": "two@example.com", "password": PLAYER_PASSWORD}
    )
    foreign = await _own_upload(other_player, storage)
    payload = {"title": "Чужое", "story": STORY, "latitude": 1, "longitude": 1}

    stolen = await player.post("/api/me/submissions", json={**payload, "assetIds": [foreign]})
    assert stolen.json()["code"] == "foreign_media"

    submission_id = (await player.post("/api/me/submissions", json=payload)).json()["id"]
    rejected = await admin_client.post(
        f"/api/admin/submissions/{submission_id}/reject", json={"comment": "Нет источника"}
    )
    assert rejected.json()["moderatorComment"] == "Нет источника"


@pytest.mark.analytics
async def test_overview_and_funnel(admin_client: Client, player: Client) -> None:
    a, b = await tagged_point(admin_client, "A"), await tagged_point(admin_client, "B")
    route = await create_route(admin_client, "stats", [(a, True, True), (b, False, True)])
    await scan(player, a)
    await scan(player, b)
    await player.post("/api/scans", json={"token": "y" * 43})

    overview = (await admin_client.get("/api/admin/analytics/overview", params={"days": 7})).json()
    assert (
        overview["scans"],
        overview["failedScans"],
        overview["runsStarted"],
        overview["runsCompleted"],
    ) == (
        2,
        1,
        1,
        1,
    )
    funnel = (await admin_client.get(f"/api/admin/analytics/routes/{route['id']}/funnel")).json()
    assert [(stop["title"], stop["visits"]) for stop in funnel["stops"]] == [("A", 1), ("B", 1)]
    points = (await admin_client.get("/api/admin/analytics/points")).json()
    assert {item["title"]: item["scans"] for item in points} == {"A": 1, "B": 1}


@pytest.mark.analytics
async def test_playback_reporting(admin_client: Client, player: Client, storage: FakeObjectStorage) -> None:
    ticket = (
        await admin_client.post(
            "/api/admin/media/uploads", json={"kind": "audio", "contentType": "audio/mpeg", "sizeBytes": 10}
        )
    ).json()
    storage.objects[ticket["uploadUrl"].removeprefix("https://storage.test/upload/")] = 10
    await admin_client.post(f"/api/admin/media/{ticket['asset']['id']}/complete")
    asset_id = ticket["asset"]["id"]
    point_id = await create_point(admin_client, "Звук", blocks=[{"kind": "audio", "assetId": asset_id}])
    token = await issue_tag(admin_client, point_id)
    report = {"pointId": point_id, "assetId": asset_id, "sessionKey": "session-0001", "durationSeconds": 100}

    await player.post(
        "/api/auth/register", json={"email": "listener@example.com", "password": PLAYER_PASSWORD}
    )
    locked = await player.post("/api/analytics/playback", json={**report, "positionSeconds": 10})
    assert locked.json()["code"] == "point_locked"

    await player.post("/api/scans", json={"token": token})
    for position in (10, 97, 40):
        response = await player.post("/api/analytics/playback", json={**report, "positionSeconds": position})
        assert response.status_code == 204

    stats = (await admin_client.get("/api/admin/analytics/playback")).json()
    assert [(item["sessions"], item["completed"], item["averageRatio"]) for item in stats] == [(1, 1, 0.97)]
