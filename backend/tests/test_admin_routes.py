"""
Integration tests for admin route builder endpoints.

Covers:
- Admin auth guard (unauthorized -> 401)
- Route CRUD (create, list, update, publish, delete)
- Stop management (add track/checkpoint stop, invalid stop, update criteria, delete)
- Checkpoint inline creation
- Track listing for route builder dropdown
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.audio_track import AudioTrack


async def _create_published_track(session: AsyncSession) -> AudioTrack:
    """Insert a published audio track directly via the DB session."""
    track = AudioTrack(
        slug="test-track-slug",
        title="Test Track",
        description="A test track",
        audio_s3_key="audio/test.mp3",
        latitude=56.8389,
        longitude=60.6057,
        moderation_status="published",
        is_published=True,
    )
    session.add(track)
    await session.commit()
    await session.refresh(track)
    return track


@pytest.mark.admin
class TestAdminAuthGuard:
    """Admin endpoints require admin session."""

    async def test_admin_unauthorized(self, test_db_client: AsyncClient):
        response = await test_db_client.get("/api/admin/routes")
        assert response.status_code == 401


@pytest.mark.admin
class TestRouteCRUD:
    """Route create / list / update / publish / delete."""

    async def test_create_route(self, admin_client: AsyncClient):
        response = await admin_client.post(
            "/api/admin/routes",
            json={"title": "Test Route", "description": "A test route"},
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["title"] == "Test Route"
        assert data["description"] == "A test route"
        assert data["is_published"] is False
        assert "id" in data
        assert "slug" in data

    async def test_list_routes_admin(self, admin_client: AsyncClient):
        create_resp = await admin_client.post(
            "/api/admin/routes",
            json={"title": "List Test Route"},
        )
        assert create_resp.status_code == 201

        response = await admin_client.get("/api/admin/routes")
        assert response.status_code == 200, response.text
        routes = response.json()["routes"]
        assert any(r["title"] == "List Test Route" for r in routes)

    async def test_update_route(self, admin_client: AsyncClient):
        create_resp = await admin_client.post(
            "/api/admin/routes",
            json={"title": "Before Update"},
        )
        route_id = create_resp.json()["id"]

        response = await admin_client.patch(
            f"/api/admin/routes/{route_id}",
            json={"title": "After Update", "description": "Updated desc"},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["title"] == "After Update"
        assert data["description"] == "Updated desc"

    async def test_publish_route(self, admin_client: AsyncClient):
        create_resp = await admin_client.post(
            "/api/admin/routes",
            json={"title": "Publishable Route"},
        )
        route_id = create_resp.json()["id"]

        response = await admin_client.patch(
            f"/api/admin/routes/{route_id}",
            json={"is_published": True},
        )
        assert response.status_code == 200
        assert response.json()["is_published"] is True

    async def test_delete_route(self, admin_client: AsyncClient):
        create_resp = await admin_client.post(
            "/api/admin/routes",
            json={"title": "To Delete"},
        )
        route_id = create_resp.json()["id"]

        response = await admin_client.delete(f"/api/admin/routes/{route_id}")
        assert response.status_code == 204

        list_resp = await admin_client.get("/api/admin/routes")
        routes = list_resp.json()["routes"]
        assert not any(r["id"] == route_id for r in routes)


@pytest.mark.admin
class TestStopManagement:
    """Stop add / update / delete within a route."""

    async def test_add_track_stop(
        self, admin_client: AsyncClient, test_db_session: AsyncSession
    ):
        track = await _create_published_track(test_db_session)

        create_resp = await admin_client.post(
            "/api/admin/routes",
            json={"title": "Route With Track Stop"},
        )
        route_id = create_resp.json()["id"]

        response = await admin_client.post(
            f"/api/admin/routes/{route_id}/stops",
            json={
                "stop_type": "track",
                "track_id": track.id,
                "completion_criteria": "scan",
            },
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["stop_type"] == "track"
        assert data["track_id"] == track.id
        assert data["completion_criteria"] == "scan"

    async def test_add_checkpoint_stop(self, admin_client: AsyncClient):
        cp_resp = await admin_client.post(
            "/api/admin/checkpoints",
            json={
                "title": "Test Checkpoint",
                "content_type": "text",
                "text_content": "Hello",
                "latitude": 56.8389,
                "longitude": 60.6057,
                "is_published": True,
            },
        )
        assert cp_resp.status_code == 201
        checkpoint_id = cp_resp.json()["id"]

        create_resp = await admin_client.post(
            "/api/admin/routes",
            json={"title": "Route With CP Stop"},
        )
        route_id = create_resp.json()["id"]

        response = await admin_client.post(
            f"/api/admin/routes/{route_id}/stops",
            json={
                "stop_type": "checkpoint",
                "checkpoint_id": checkpoint_id,
                "completion_criteria": "scan",
            },
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["stop_type"] == "checkpoint"
        assert data["checkpoint_id"] == checkpoint_id

    async def test_add_stop_invalid_no_track_id(self, admin_client: AsyncClient):
        create_resp = await admin_client.post(
            "/api/admin/routes",
            json={"title": "Invalid Stop Route"},
        )
        route_id = create_resp.json()["id"]

        response = await admin_client.post(
            f"/api/admin/routes/{route_id}/stops",
            json={"stop_type": "track", "completion_criteria": "scan"},
        )
        assert response.status_code == 400
        assert "track_id is required" in response.json()["detail"]

    async def test_update_stop_criteria(
        self, admin_client: AsyncClient, test_db_session: AsyncSession
    ):
        track = await _create_published_track(test_db_session)

        create_resp = await admin_client.post(
            "/api/admin/routes",
            json={"title": "Update Stop Route"},
        )
        route_id = create_resp.json()["id"]

        stop_resp = await admin_client.post(
            f"/api/admin/routes/{route_id}/stops",
            json={"stop_type": "track", "track_id": track.id},
        )
        stop_id = stop_resp.json()["id"]

        response = await admin_client.patch(
            f"/api/admin/routes/{route_id}/stops/{stop_id}",
            json={"completion_criteria": "listen_95"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["completion_criteria"] == "listen_95"

    async def test_delete_stop(
        self, admin_client: AsyncClient, test_db_session: AsyncSession
    ):
        track = await _create_published_track(test_db_session)

        create_resp = await admin_client.post(
            "/api/admin/routes",
            json={"title": "Delete Stop Route"},
        )
        route_id = create_resp.json()["id"]

        stop_resp = await admin_client.post(
            f"/api/admin/routes/{route_id}/stops",
            json={"stop_type": "track", "track_id": track.id},
        )
        stop_id = stop_resp.json()["id"]

        response = await admin_client.delete(
            f"/api/admin/routes/{route_id}/stops/{stop_id}"
        )
        assert response.status_code == 204

        list_resp = await admin_client.get(
            f"/api/admin/routes/{route_id}/stops"
        )
        stops = list_resp.json()
        assert not any(s["id"] == stop_id for s in stops)


@pytest.mark.admin
class TestCheckpointInline:
    """Checkpoint creation via admin route builder."""

    async def test_create_checkpoint(self, admin_client: AsyncClient):
        response = await admin_client.post(
            "/api/admin/checkpoints",
            json={
                "title": "Inline Checkpoint",
                "content_type": "text",
                "text_content": "Some text",
                "latitude": 56.8389,
                "longitude": 60.6057,
                "is_published": True,
            },
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["title"] == "Inline Checkpoint"
        assert data["content_type"] == "text"
        assert data["is_published"] is True
        assert "slug" in data

    async def test_list_checkpoints(self, admin_client: AsyncClient):
        await admin_client.post(
            "/api/admin/checkpoints",
            json={"title": "CP For Listing", "content_type": "text", "latitude": 56.8389, "longitude": 60.6057},
        )

        response = await admin_client.get("/api/admin/checkpoints")
        assert response.status_code == 200
        checkpoints = response.json()["checkpoints"]
        assert any(cp["title"] == "CP For Listing" for cp in checkpoints)

    async def test_create_checkpoint_without_coordinates_returns_422(
        self, admin_client: AsyncClient
    ):
        response = await admin_client.post(
            "/api/admin/checkpoints",
            json={"title": "No Coords CP", "content_type": "text"},
        )
        assert response.status_code == 422


@pytest.mark.admin
class TestTrackListing:
    """Track listing for route builder dropdown."""

    async def test_list_tracks_admin(
        self, admin_client: AsyncClient, test_db_session: AsyncSession
    ):
        await _create_published_track(test_db_session)

        response = await admin_client.get("/api/admin/tracks")
        assert response.status_code == 200, response.text
        tracks = response.json()["tracks"]
        assert any(t["slug"] == "test-track-slug" for t in tracks)
