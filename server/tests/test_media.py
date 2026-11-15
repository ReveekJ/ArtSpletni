import pytest

from tests.conftest import Client
from tests.fakes import FakeObjectStorage

pytestmark = pytest.mark.media


async def test_upload_lifecycle(admin_client: Client, storage: FakeObjectStorage) -> None:
    started = await admin_client.post(
        "/api/admin/media/uploads",
        json={"kind": "audio", "contentType": "audio/mpeg", "sizeBytes": 1000, "filename": "a.mp3"},
    )
    assert started.status_code == 201, started.text
    ticket = started.json()
    asset_id = ticket["asset"]["id"]
    key = ticket["uploadUrl"].removeprefix("https://storage.test/upload/")
    assert key.startswith("private/audio/") and key.endswith(".mp3")

    missing = await admin_client.post(f"/api/admin/media/{asset_id}/complete")
    assert missing.status_code == 400
    assert missing.json()["code"] == "upload_missing"

    storage.objects[key] = 900
    completed = await admin_client.post(f"/api/admin/media/{asset_id}/complete")
    assert completed.status_code == 200
    body = completed.json()
    assert body["status"] == "ready"
    assert body["sizeBytes"] == 900
    assert body["url"].endswith("ttl=900")

    assert (await admin_client.delete(f"/api/admin/media/{asset_id}")).status_code == 204
    assert storage.deleted == [key]
    assert (await admin_client.get(f"/api/admin/media/{asset_id}")).status_code == 404


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        ({"kind": "image", "contentType": "image/gif", "sizeBytes": 10}, "unsupported_media_type"),
        ({"kind": "image", "contentType": "image/png", "sizeBytes": 16 * 1024 * 1024}, "media_too_large"),
    ],
)
async def test_upload_validation(
    admin_client: Client, storage: FakeObjectStorage, payload: dict[str, str | int], code: str
) -> None:
    response = await admin_client.post("/api/admin/media/uploads", json=payload)
    assert response.status_code == 400
    assert response.json()["code"] == code


async def test_oversized_upload_is_rejected_on_complete(
    admin_client: Client, storage: FakeObjectStorage
) -> None:
    ticket = (
        await admin_client.post(
            "/api/admin/media/uploads",
            json={"kind": "image", "contentType": "image/png", "sizeBytes": 100, "isPublic": True},
        )
    ).json()
    key = ticket["uploadUrl"].removeprefix("https://storage.test/upload/")
    storage.objects[key] = 20 * 1024 * 1024

    response = await admin_client.post(f"/api/admin/media/{ticket['asset']['id']}/complete")

    assert response.json()["code"] == "media_too_large"
    assert storage.deleted == [key]
