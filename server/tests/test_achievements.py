from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Unlock
from app.domain.achievements.cli import _seed
from app.domain.achievements.services import _in_window
from tests.helpers import Client, create_route, scan, tagged_point

pytestmark = pytest.mark.achievements


async def create_achievement(
    admin: Client, code: str, rule: str, params: dict[str, object], **extra: object
) -> str:
    response = await admin.post(
        "/api/admin/achievements",
        json={"code": code, "title": {"ru": code}, "rule": rule, "params": params, **extra},
    )
    assert response.status_code == 201, response.text
    achievement_id: str = response.json()["id"]
    return achievement_id


async def test_seeded_first_gossip_and_progress(admin_client: Client, player: Client) -> None:
    assert await _seed() == 12
    assert await _seed() == 0
    point = await tagged_point(admin_client, "A")

    body = await scan(player, point)

    assert [(item["kind"], item["title"]) for item in body["notifications"]] == [
        ("achievement_earned", "Первая сплетня")
    ]
    mine = {item["code"]: item for item in (await player.get("/api/me/achievements")).json()}
    assert mine["first_gossip"]["earnedAt"] is not None
    assert mine["gossip_collector"]["progress"] == {"current": 1, "target": 10}
    assert "night_gossip" not in mine
    assert mine["gossip_collector"]["title"] == "Собиратель слухов"


async def test_route_achievement_grants_reward_offer(admin_client: Client, player: Client) -> None:
    partner_id = (await admin_client.post("/api/admin/partners", json={"name": "Бар"})).json()["id"]
    reward = (
        await admin_client.post(
            "/api/admin/offers", json={"partnerId": partner_id, "title": {"ru": "Шот за маршрут"}}
        )
    ).json()["id"]
    a = await tagged_point(admin_client, "A")
    route = await create_route(admin_client, "bar", [(a, True, True)])
    await create_achievement(
        admin_client, "bar_route", "route_completed", {"routeId": route["id"]}, rewardOfferId=reward
    )
    await create_achievement(admin_client, "fast", "route_completed_within", {"hours": 1})
    await create_achievement(admin_client, "pioneer", "route_first_finishers", {"count": 1})

    body = await scan(player, a)

    kinds = sorted((item["kind"], item["title"]) for item in body["notifications"])
    assert kinds == [
        ("achievement_earned", "bar_route"),
        ("achievement_earned", "fast"),
        ("achievement_earned", "pioneer"),
        ("offer_granted", "Шот за маршрут"),
    ]
    offers = (await player.get("/api/me/offers")).json()
    assert [offer["title"] for offer in offers] == ["Шот за маршрут"]


async def test_first_finishers_limit(admin_client: Client, player: Client, other_player: Client) -> None:
    a = await tagged_point(admin_client, "A")
    await create_route(admin_client, "race", [(a, True, True)])
    await create_achievement(admin_client, "pioneer", "route_first_finishers", {"count": 1})

    first = await scan(player, a)
    second = await scan(other_player, a)

    assert [item["kind"] for item in first["notifications"]] == ["achievement_earned"]
    assert second["notifications"] == []


async def test_days_streak(admin_client: Client, player: Client, db_session: AsyncSession) -> None:
    await create_achievement(admin_client, "streak", "days_streak", {"days": 3})
    points = [await tagged_point(admin_client, name) for name in ("D1", "D2", "D3")]
    for days_ago, point in ((2, points[0]), (1, points[1])):
        await scan(player, point)
        await db_session.execute(
            update(Unlock)
            .where(Unlock.point_id == point.id)
            .values(created_at=datetime.now(UTC) - timedelta(days=days_ago))
        )
        await db_session.commit()

    body = await scan(player, points[2])

    assert [item["title"] for item in body["notifications"]] == ["streak"]


async def test_redemption_achievement(admin_client: Client, player: Client, other_player: Client) -> None:
    await create_achievement(admin_client, "regular", "offers_redeemed", {"count": 1})
    partner_id = (await admin_client.post("/api/admin/partners", json={"name": "Кафе"})).json()["id"]
    reward = (
        await admin_client.post("/api/admin/offers", json={"partnerId": partner_id, "title": {"ru": "Кофе"}})
    ).json()["id"]
    await create_achievement(
        admin_client, "first_scan", "points_unlocked", {"count": 1}, rewardOfferId=reward
    )
    await other_player.post(
        "/api/auth/register", json={"email": "staff@cafe.test", "password": "staff-password"}
    )
    await admin_client.post(f"/api/admin/partners/{partner_id}/members", json={"email": "staff@cafe.test"})
    await scan(player, await tagged_point(admin_client, "A"))
    grant_id = (await player.get("/api/me/offers")).json()[0]["grantId"]
    code = (await player.post(f"/api/me/offers/{grant_id}/qr")).json()["code"]

    await other_player.post(f"/api/partner/{partner_id}/redemptions", json={"code": code})

    mine = {item["code"]: item for item in (await player.get("/api/me/achievements")).json()}
    assert mine["regular"]["earnedAt"] is not None


async def test_invalid_rule_params(admin_client: Client) -> None:
    response = await admin_client.post(
        "/api/admin/achievements",
        json={"code": "bad", "title": {"ru": "x"}, "rule": "points_unlocked", "params": {"days": 3}},
    )
    assert response.json()["code"] == "invalid_rule_params"


def test_time_window_wraps_midnight() -> None:
    assert _in_window(23, 23, 5)
    assert _in_window(2, 23, 5)
    assert not _in_window(5, 23, 5)
    assert _in_window(14, 12, 18)
    assert not _in_window(18, 12, 18)
