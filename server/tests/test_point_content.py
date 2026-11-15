import pytest

from tests.fakes import FakeObjectStorage
from tests.helpers import Client, create_point, issue_tag

pytestmark = pytest.mark.points


async def _ready_asset(admin: Client, storage: FakeObjectStorage, kind: str, content_type: str) -> str:
    ticket = (
        await admin.post(
            "/api/admin/media/uploads", json={"kind": kind, "contentType": content_type, "sizeBytes": 10}
        )
    ).json()
    storage.objects[ticket["uploadUrl"].removeprefix("https://storage.test/upload/")] = 10
    await admin.post(f"/api/admin/media/{ticket['asset']['id']}/complete")
    asset_id: str = ticket["asset"]["id"]
    return asset_id


async def test_media_blocks_use_language_variants(
    admin_client: Client, player: Client, storage: FakeObjectStorage
) -> None:
    base_audio = await _ready_asset(admin_client, storage, "audio", "audio/mpeg")
    english_audio = await _ready_asset(admin_client, storage, "audio", "audio/mpeg")
    point_id = await create_point(
        admin_client,
        "Голос",
        blocks=[
            {"kind": "text", "text": {"ru": "Слушай", "en": "Listen"}},
            {"kind": "audio", "assetId": base_audio, "mediaVariants": {"en": english_audio}},
        ],
    )
    token = await issue_tag(admin_client, point_id)
    await player.post("/api/scans", json={"token": token})

    russian = (await player.get(f"/api/points/{point_id}")).json()
    english = (await player.get(f"/api/points/{point_id}", params={"lang": "en"})).json()
    chinese = (
        await player.get(f"/api/points/{point_id}", headers={"Accept-Language": "zh-CN,zh;q=0.9"})
    ).json()

    assert russian["blocks"][0]["text"] == "Слушай"
    assert english["blocks"][0]["text"] == "Listen"
    assert chinese["blocks"][0]["text"] == "[zh] Слушай"
    assert russian["blocks"][1]["mediaUrl"] != english["blocks"][1]["mediaUrl"]
    assert chinese["blocks"][1]["mediaUrl"] == russian["blocks"][1]["mediaUrl"]


async def test_media_kind_must_match_block(admin_client: Client, storage: FakeObjectStorage) -> None:
    image = await _ready_asset(admin_client, storage, "image", "image/png")

    response = await admin_client.post(
        "/api/admin/points",
        json={
            "kind": "gossip",
            "title": {"ru": "Т"},
            "latitude": 1,
            "longitude": 1,
            "blocks": [{"kind": "audio", "assetId": image}],
        },
    )

    assert response.json()["code"] == "media_kind_mismatch"


async def test_human_translation_survives_point_update(admin_client: Client) -> None:
    point_id = await create_point(admin_client, "Дом")
    detail = (await admin_client.get(f"/api/admin/points/{point_id}")).json()
    payload = {
        "kind": "gossip",
        "title": {"ru": "Дом купца", "en": "Merchant house", "zh": detail["title"]["zh"]["text"]},
        "latitude": 1,
        "longitude": 1,
        "isPublished": True,
        "blocks": [{"kind": "text", "text": {"ru": "т"}}],
    }

    updated = (await admin_client.put(f"/api/admin/points/{point_id}", json=payload)).json()

    assert updated["title"]["en"] == {"text": "Merchant house", "machine": False}
    assert updated["title"]["zh"] == {"text": "[zh] Дом купца", "machine": True}
