"""
Integration tests for admin track CRUD endpoints.

Covers:
- Create track (auto-published, with/without cover, invalid format)
- Get track detail
- Update track metadata and file replacement
- Delete track
- Unauthorized access
"""

import io

import pytest
from httpx import AsyncClient

VALID_MP3 = (
    b"ID3\x03\x00\x00\x00\x00\x00\x21"
    b"\x00\x00\x00LAME3.99r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
)
VALID_PNG = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01\x5d\xcc\xdb\x92"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.mark.admin
class TestAdminTrackCRUD:
    """Admin track create / get / update / delete."""

    async def test_create_track_auto_published(self, admin_client: AsyncClient):
        files = {"audio_file": ("test.mp3", VALID_MP3, "audio/mpeg")}
        data = {
            "title": "Admin Track",
            "description": "Created via admin",
            "author": "Admin",
            "latitude": "55.7558",
            "longitude": "37.6173",
            "location_name": "Moscow",
        }
        response = await admin_client.post(
            "/api/admin/tracks",
            files=files,
            data=data,
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["title"] == "Admin Track"
        assert body["moderation_status"] == "published"
        assert body["is_published"] is True
        assert body["published_at"] is not None
        assert body["audio_url"].startswith("http")
        assert body["cover_url"] is None
        assert body["slug"]
        track_id = body["id"]

        detail = await admin_client.get(f"/api/admin/tracks/{track_id}")
        assert detail.status_code == 200
        assert detail.json()["id"] == track_id

    async def test_create_track_with_cover(self, admin_client: AsyncClient):
        files = {
            "audio_file": ("song.mp3", VALID_MP3, "audio/mpeg"),
            "cover_file": ("cover.png", VALID_PNG, "image/png"),
        }
        data = {"title": "Track With Cover", "latitude": "56.8389", "longitude": "60.6057"}
        response = await admin_client.post(
            "/api/admin/tracks",
            files=files,
            data=data,
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["cover_url"] is not None
        assert body["cover_url"].startswith("http")

    async def test_create_track_invalid_audio_format(self, admin_client: AsyncClient):
        files = {"audio_file": ("test.txt", b"not audio", "text/plain")}
        data = {"title": "Bad Format", "latitude": "56.8389", "longitude": "60.6057"}
        response = await admin_client.post(
            "/api/admin/tracks",
            files=files,
            data=data,
        )
        assert response.status_code == 415

    async def test_create_track_empty_audio(self, admin_client: AsyncClient):
        files = {"audio_file": ("empty.mp3", b"", "audio/mpeg")}
        data = {"title": "Empty Audio", "latitude": "56.8389", "longitude": "60.6057"}
        response = await admin_client.post(
            "/api/admin/tracks",
            files=files,
            data=data,
        )
        assert response.status_code == 422

    async def test_get_track_not_found(self, admin_client: AsyncClient):
        response = await admin_client.get("/api/admin/tracks/999999")
        assert response.status_code == 404

    async def test_list_tracks(self, admin_client: AsyncClient):
        files = {"audio_file": ("list.mp3", VALID_MP3, "audio/mpeg")}
        data = {"title": "Track For Listing", "latitude": "56.8389", "longitude": "60.6057"}
        create_resp = await admin_client.post(
            "/api/admin/tracks",
            files=files,
            data=data,
        )
        assert create_resp.status_code == 201

        response = await admin_client.get("/api/admin/tracks")
        assert response.status_code == 200
        tracks = response.json()["tracks"]
        assert any(t["title"] == "Track For Listing" for t in tracks)
        listed = next(t for t in tracks if t["title"] == "Track For Listing")
        assert listed["description"] is None
        assert listed["author"] is None
        assert listed["moderation_status"] == "published"

    async def test_update_track_metadata(self, admin_client: AsyncClient):
        files = {"audio_file": ("orig.mp3", VALID_MP3, "audio/mpeg")}
        data = {"title": "Original Title", "latitude": "56.8389", "longitude": "60.6057"}
        create_resp = await admin_client.post(
            "/api/admin/tracks",
            files=files,
            data=data,
        )
        track_id = create_resp.json()["id"]

        update_data = {
            "title": "Updated Title",
            "description": "New description",
            "author": "New Author",
        }
        response = await admin_client.patch(
            f"/api/admin/tracks/{track_id}",
            data=update_data,
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["title"] == "Updated Title"
        assert body["description"] == "New description"
        assert body["author"] == "New Author"

    async def test_update_track_replace_audio(self, admin_client: AsyncClient):
        files = {"audio_file": ("orig.mp3", VALID_MP3, "audio/mpeg")}
        data = {"title": "Replace Audio Track", "latitude": "56.8389", "longitude": "60.6057"}
        create_resp = await admin_client.post(
            "/api/admin/tracks",
            files=files,
            data=data,
        )
        track_id = create_resp.json()["id"]
        original_url = create_resp.json()["audio_url"]

        new_files = {"audio_file": ("replacement.mp3", VALID_MP3, "audio/mpeg")}
        response = await admin_client.patch(
            f"/api/admin/tracks/{track_id}",
            files=new_files,
            data={"title": "Replace Audio Track"},
        )
        assert response.status_code == 200, response.text
        new_url = response.json()["audio_url"]
        assert new_url != original_url

    async def test_update_track_add_cover(self, admin_client: AsyncClient):
        files = {"audio_file": ("nocover.mp3", VALID_MP3, "audio/mpeg")}
        data = {"title": "No Cover Track", "latitude": "56.8389", "longitude": "60.6057"}
        create_resp = await admin_client.post(
            "/api/admin/tracks",
            files=files,
            data=data,
        )
        track_id = create_resp.json()["id"]
        assert create_resp.json()["cover_url"] is None

        cover_files = {
            "cover_file": ("cover.png", VALID_PNG, "image/png"),
        }
        response = await admin_client.patch(
            f"/api/admin/tracks/{track_id}",
            files=cover_files,
            data={"title": "No Cover Track"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["cover_url"] is not None

    async def test_delete_track(self, admin_client: AsyncClient):
        files = {"audio_file": ("delete.mp3", VALID_MP3, "audio/mpeg")}
        data = {"title": "Track To Delete", "latitude": "56.8389", "longitude": "60.6057"}
        create_resp = await admin_client.post(
            "/api/admin/tracks",
            files=files,
            data=data,
        )
        track_id = create_resp.json()["id"]

        delete_resp = await admin_client.delete(f"/api/admin/tracks/{track_id}")
        assert delete_resp.status_code == 204

        get_resp = await admin_client.get(f"/api/admin/tracks/{track_id}")
        assert get_resp.status_code == 404

    async def test_delete_track_not_found(self, admin_client: AsyncClient):
        response = await admin_client.delete("/api/admin/tracks/999999")
        assert response.status_code == 404

    async def test_create_unauthorized(self, test_db_client: AsyncClient):
        files = {"audio_file": ("test.mp3", VALID_MP3, "audio/mpeg")}
        data = {"title": "Unauthorized Track", "latitude": "56.8389", "longitude": "60.6057"}
        response = await test_db_client.post(
            "/api/admin/tracks",
            files=files,
            data=data,
        )
        assert response.status_code == 401

    async def test_create_track_without_coordinates_returns_422(
        self, admin_client: AsyncClient
    ):
        files = {"audio_file": ("no-coords.mp3", VALID_MP3, "audio/mpeg")}
        data = {"title": "No Coords Track"}
        response = await admin_client.post(
            "/api/admin/tracks",
            files=files,
            data=data,
        )
        assert response.status_code == 422
