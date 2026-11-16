from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.gossip.deps import build_generation_service
from app.domain.gossip.llm import GossipWriterError
from app.domain.gossip.repositories import GossipGenerationRepository
from app.lib.settings import get_settings
from tests.conftest import register
from tests.fakes import GossipFakes
from tests.helpers import Client, TaggedPoint, scan, tagged_point

pytestmark = pytest.mark.gossip


async def _unlocked_point(admin: Client, player: Client, title: str = "Башня") -> TaggedPoint:
    point = await tagged_point(admin, title)
    await scan(player, point)
    return point


async def _feed(player: Client, point: TaggedPoint, lang: str | None = None) -> dict[str, Any]:
    response = await player.get(f"/api/points/{point.id}/gossip", params={"lang": lang} if lang else None)
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


async def test_locked_point_has_no_gossip(admin_client: Client, player: Client, gossip: GossipFakes) -> None:
    point = await tagged_point(admin_client, "Закрытая")
    await register(player, "locked@spletni.test")

    response = await player.get(f"/api/points/{point.id}/gossip")

    assert response.status_code == 403
    assert response.json()["code"] == "point_locked"
    assert gossip.writer.calls == 0


async def test_first_view_generates_once(admin_client: Client, player: Client, gossip: GossipFakes) -> None:
    point = await _unlocked_point(admin_client, player)

    first = await _feed(player, point)
    second = await _feed(player, point)

    assert first["status"] == "pending"
    assert second["status"] == "done"
    assert [item["title"] for item in second["items"]] == ["Ghost ru", "Kiss ru"]
    await _feed(player, point)
    assert gossip.writer.calls == 1


async def test_language_selection_and_fallback(admin_client: Client, player: Client) -> None:
    point = await _unlocked_point(admin_client, player)
    await _feed(player, point)

    english = await _feed(player, point, "en")
    chinese = await _feed(player, point, "zh")
    unsupported = await _feed(player, point, "de")

    assert [item["title"] for item in english["items"]] == ["Ghost en", "Kiss en"]
    assert chinese["items"][0]["text"] == "Ghost text zh"
    assert unsupported["items"][0]["title"] == "Ghost ru"


async def test_items_carry_photo_sources_and_downgraded_veracity(
    admin_client: Client, player: Client
) -> None:
    point = await _unlocked_point(admin_client, player)
    await _feed(player, point)

    ghost, kiss = (await _feed(player, point))["items"]

    assert ghost["veracity"] == "legend"
    assert ghost["placeName"] == "Old Tower"
    assert ghost["distanceM"] == 120
    assert ghost["photo"] == {
        "url": "https://upload.wikimedia.org/old_tower_800.jpg",
        "author": "Jane Doe",
        "license": "CC BY-SA 4.0",
        "sourceUrl": "https://commons.wikimedia.org/wiki/File:Old_tower.jpg",
    }
    assert [(source["origin"], source["url"]) for source in ghost["sources"]] == [
        ("wikipedia", "https://en.wikipedia.org/wiki/Old_Tower"),
        ("llm_web", "https://example.com/alive"),
    ]
    assert kiss["veracity"] == "unverified"
    assert kiss["photo"] is None
    assert kiss["sources"] == []
    assert kiss["placeName"] == "Bench by the river"


async def test_failed_generation_keeps_items_and_is_not_retried_immediately(
    admin_client: Client, player: Client, gossip: GossipFakes
) -> None:
    point = await _unlocked_point(admin_client, player)
    await _feed(player, point)
    assert (await _feed(player, point))["status"] == "done"
    gossip.writer.error = GossipWriterError("LLM is down")

    regenerate = await admin_client.post(f"/api/admin/points/{point.id}/gossip/regenerate")
    assert regenerate.status_code == 202
    calls = gossip.writer.calls

    admin_feed = (await admin_client.get(f"/api/admin/points/{point.id}/gossip")).json()
    assert admin_feed["status"] == "failed"
    assert "LLM is down" in admin_feed["error"]
    assert len(admin_feed["items"]) == 2
    feed = await _feed(player, point)
    assert feed["status"] == "failed"
    assert len(feed["items"]) == 2
    assert gossip.writer.calls == calls


async def test_moved_point_is_regenerated(admin_client: Client, player: Client, gossip: GossipFakes) -> None:
    point = await _unlocked_point(admin_client, player)
    await _feed(player, point)
    await _feed(player, point)
    assert len(gossip.nearby.calls) == 1

    stored = (await admin_client.get(f"/api/admin/points/{point.id}")).json()
    update = {key: stored[key] for key in ("kind", "latitude", "longitude", "isPublished")}
    update["title"] = {"ru": stored["title"]["ru"]["text"]}
    update["latitude"] = 56.84
    update["blocks"] = [{"kind": "text", "text": {"ru": "x"}}]
    assert (await admin_client.put(f"/api/admin/points/{point.id}", json=update)).status_code == 200

    assert (await _feed(player, point))["status"] == "pending"
    assert (await _feed(player, point))["status"] == "done"
    assert gossip.nearby.calls[-1][0] == 56.84


async def test_hidden_items_are_not_shown_to_players(admin_client: Client, player: Client) -> None:
    point = await _unlocked_point(admin_client, player)
    await _feed(player, point)
    admin_items = (await admin_client.get(f"/api/admin/points/{point.id}/gossip")).json()["items"]

    response = await admin_client.patch(f"/api/admin/gossip/{admin_items[0]['id']}", json={"isHidden": True})

    assert response.status_code == 200
    assert response.json()["isHidden"] is True
    assert set(response.json()["translations"]) == {"ru", "en", "zh"}
    visible = await _feed(player, point)
    assert [item["id"] for item in visible["items"]] == [admin_items[1]["id"]]
    after = (await admin_client.get(f"/api/admin/points/{point.id}/gossip")).json()
    assert len(after["items"]) == 2


async def test_unknown_item_and_point_return_404(admin_client: Client) -> None:
    assert (
        await admin_client.patch(f"/api/admin/gossip/{uuid4()}", json={"isHidden": True})
    ).status_code == 404
    assert (await admin_client.get(f"/api/admin/points/{uuid4()}/gossip")).status_code == 404
    assert (await admin_client.post(f"/api/admin/points/{uuid4()}/gossip/regenerate")).status_code == 404


async def test_disabled_llm_skips_generation(
    admin_client: Client, player: Client, gossip: GossipFakes, monkeypatch: pytest.MonkeyPatch
) -> None:
    point = await _unlocked_point(admin_client, player)
    disabled = get_settings().model_copy(update={"llm": None})
    monkeypatch.setattr("app.domain.gossip.deps.get_settings", lambda: disabled)

    feed = await _feed(player, point)
    regenerate = await admin_client.post(f"/api/admin/points/{point.id}/gossip/regenerate")
    admin_feed = (await admin_client.get(f"/api/admin/points/{point.id}/gossip")).json()

    assert feed == {"status": "none", "items": []}
    assert regenerate.status_code == 503
    assert regenerate.json()["code"] == "llm_not_configured"
    assert admin_feed["enabled"] is False
    assert gossip.writer.calls == 0


async def test_superseded_attempt_is_discarded(
    admin_client: Client, player: Client, db_session: AsyncSession, gossip: GossipFakes
) -> None:
    point = await _unlocked_point(admin_client, player)
    await _feed(player, point)
    await _feed(player, point)
    point_id = UUID(point.id)
    generations = GossipGenerationRepository(session=db_session)
    generation = await generations.get_one(point_id=point_id)
    restarted = await generations.restart(generation, generation.latitude, generation.longitude)
    assert restarted is not None
    await db_session.commit()
    calls = gossip.writer.calls

    await build_generation_service(db_session).generate(point_id, uuid4())

    assert gossip.writer.calls == calls
    assert (await generations.get_one(point_id=point_id)).status.value == "pending"


async def test_concurrent_claim_creates_one_generation(
    admin_client: Client, db_session: AsyncSession
) -> None:
    point = await tagged_point(admin_client, "Гонка")
    generations = GossipGenerationRepository(session=db_session)

    first = await generations.create_pending(UUID(point.id), 55.75, 37.61)
    second = await generations.create_pending(UUID(point.id), 55.75, 37.61)

    assert first is not None
    assert second is None
