from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OfferGrant
from tests.conftest import PLAYER_PASSWORD
from tests.helpers import Client, TaggedPoint, create_point, issue_tag, scan

pytestmark = pytest.mark.offers

STAFF_EMAIL = "barista@cafe.test"


@dataclass(frozen=True, slots=True)
class PartnerSetup:
    partner_id: str
    point: TaggedPoint
    offer_id: str


async def setup_partner(
    admin: Client, staff: Client, *, limit: int | None = None, valid_until: datetime | None = None
) -> PartnerSetup:
    partner_id = (await admin.post("/api/admin/partners", json={"name": "Кафе «Сплетница»"})).json()["id"]
    point_id = await create_point(
        admin,
        "Кафе",
        kind="partner",
        blocks=[],
        note={"ru": "Подойди к бару и скажи «сплетница»"},
        partner_id=partner_id,
    )
    offer = await admin.post(
        "/api/admin/offers",
        json={
            "partnerId": partner_id,
            "pointId": point_id,
            "title": {"ru": "Кофе в подарок"},
            "promoCode": "SPLETNI10",
            "redemptionLimit": limit,
            "validUntil": valid_until.isoformat() if valid_until else None,
        },
    )
    assert offer.status_code == 201, offer.text
    await staff.post("/api/auth/register", json={"email": STAFF_EMAIL, "password": PLAYER_PASSWORD})
    member = await admin.post(f"/api/admin/partners/{partner_id}/members", json={"email": STAFF_EMAIL})
    assert member.status_code == 201, member.text
    token = await issue_tag(admin, point_id)
    return PartnerSetup(partner_id, TaggedPoint(point_id, token), offer.json()["id"])


async def test_scan_grants_offer_once(admin_client: Client, player: Client, other_player: Client) -> None:
    setup = await setup_partner(admin_client, other_player)

    first = await scan(player, setup.point)
    second = await scan(player, setup.point)

    assert [item["kind"] for item in first["notifications"]] == ["offer_granted"]
    assert first["notifications"][0]["title"] == "Кофе в подарок"
    assert second["notifications"] == []
    offers = (await player.get("/api/me/offers")).json()
    assert len(offers) == 1
    assert offers[0]["promoCode"] == "SPLETNI10"
    assert offers[0]["status"] == "active"
    assert offers[0]["partnerName"] == "Кафе «Сплетница»"
    content = (await player.get(f"/api/points/{setup.point.id}")).json()
    assert content["note"] == "Подойди к бару и скажи «сплетница»"


async def test_qr_redemption_flow(admin_client: Client, player: Client, other_player: Client) -> None:
    staff = other_player
    setup = await setup_partner(admin_client, staff)
    await scan(player, setup.point)
    grant_id = (await player.get("/api/me/offers")).json()[0]["grantId"]
    qr = (await player.post(f"/api/me/offers/{grant_id}/qr")).json()

    assert [partner["id"] for partner in (await staff.get("/api/partner")).json()] == [setup.partner_id]
    lookup = await staff.post(
        f"/api/partner/{setup.partner_id}/redemptions/lookup", json={"token": qr["token"]}
    )
    assert lookup.json()["status"] == "active"

    redeemed = await staff.post(f"/api/partner/{setup.partner_id}/redemptions", json={"token": qr["token"]})
    assert redeemed.status_code == 200
    assert redeemed.json()["status"] == "redeemed"

    again = await staff.post(
        f"/api/partner/{setup.partner_id}/redemptions", json={"code": qr["code"].lower()}
    )
    assert again.status_code == 409
    assert again.json()["code"] == "grant_redeemed"
    assert (await player.get("/api/me/offers")).json()[0]["status"] == "redeemed"

    stats = (await staff.get(f"/api/partner/{setup.partner_id}/stats")).json()
    assert (stats[0]["granted"], stats[0]["redeemed"]) == (1, 1)
    recent = (await staff.get(f"/api/partner/{setup.partner_id}/redemptions")).json()
    assert [row["grantId"] for row in recent] == [grant_id]


async def test_redemption_requires_membership(
    admin_client: Client, player: Client, other_player: Client
) -> None:
    setup = await setup_partner(admin_client, other_player)
    await scan(player, setup.point)
    await player.post(
        "/api/auth/register", json={"email": "not-staff@example.com", "password": PLAYER_PASSWORD}
    )
    code = (
        await player.post(f"/api/me/offers/{(await player.get('/api/me/offers')).json()[0]['grantId']}/qr")
    ).json()["code"]

    response = await player.post(f"/api/partner/{setup.partner_id}/redemptions", json={"code": code})

    assert response.status_code == 403
    assert response.json()["code"] == "not_partner_member"


async def test_invalid_qr_token(admin_client: Client, other_player: Client) -> None:
    setup = await setup_partner(admin_client, other_player)

    response = await other_player.post(
        f"/api/partner/{setup.partner_id}/redemptions", json={"token": "forged.123.signature"}
    )

    assert response.json()["code"] == "invalid_qr_token"


async def test_redemption_limit(admin_client: Client, app_clients: list[Client]) -> None:
    staff, first, second, third = app_clients
    setup = await setup_partner(admin_client, staff, limit=1)
    await scan(first, setup.point)
    await scan(second, setup.point)
    codes = []
    for player in (first, second):
        grant_id = (await player.get("/api/me/offers")).json()[0]["grantId"]
        codes.append((await player.post(f"/api/me/offers/{grant_id}/qr")).json()["code"])

    assert (
        await staff.post(f"/api/partner/{setup.partner_id}/redemptions", json={"code": codes[0]})
    ).status_code == 200
    exhausted = await staff.post(f"/api/partner/{setup.partner_id}/redemptions", json={"code": codes[1]})
    assert exhausted.json()["code"] == "grant_exhausted"

    late = await scan(third, setup.point)
    assert late["notifications"] == []
    assert (await third.get("/api/me/offers")).json() == []


async def test_expired_offers(
    admin_client: Client, player: Client, other_player: Client, db_session: AsyncSession
) -> None:
    setup = await setup_partner(admin_client, other_player, valid_until=datetime.now(UTC) + timedelta(days=1))
    await scan(player, setup.point)
    grant_id = (await player.get("/api/me/offers")).json()[0]["grantId"]
    await db_session.execute(
        update(OfferGrant)
        .where(OfferGrant.offer_id == setup.offer_id)
        .values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
    )
    await db_session.commit()
    code = (await player.post(f"/api/me/offers/{grant_id}/qr")).json()["code"]

    response = await other_player.post(f"/api/partner/{setup.partner_id}/redemptions", json={"code": code})

    assert response.json()["code"] == "grant_expired"
    assert (await player.get("/api/me/offers")).json()[0]["status"] == "expired"


async def test_guest_offer_moves_to_account(
    admin_client: Client, player: Client, other_player: Client
) -> None:
    setup = await setup_partner(admin_client, other_player)
    await scan(player, setup.point)

    await player.post("/api/auth/login", json={"email": STAFF_EMAIL, "password": PLAYER_PASSWORD})

    assert len((await player.get("/api/me/offers")).json()) == 1


async def test_offer_admin_validation(admin_client: Client, other_player: Client) -> None:
    setup = await setup_partner(admin_client, other_player)
    gossip_point = await create_point(admin_client, "Сплетня")

    duplicate = await admin_client.post(
        "/api/admin/offers",
        json={"partnerId": setup.partner_id, "pointId": setup.point.id, "title": {"ru": "Ещё"}},
    )
    mismatch = await admin_client.post(
        "/api/admin/offers",
        json={"partnerId": setup.partner_id, "pointId": gossip_point, "title": {"ru": "Не туда"}},
    )

    assert duplicate.json()["code"] == "point_has_offer"
    assert mismatch.json()["code"] == "offer_point_mismatch"
