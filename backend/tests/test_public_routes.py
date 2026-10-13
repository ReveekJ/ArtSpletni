"""
Integration tests for public route endpoints.

Covers:
- GET /api/routes (list published only, empty list)
- GET /api/routes/{slug} (detail with stops, not found, unpublished)
- Route detail includes explicit dependencies between stops
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.audio_track import AudioTrack


async def _create_published_track(session: AsyncSession, slug: str = "pub-track") -> AudioTrack:
    track = AudioTrack(
        slug=slug,
        title=f"Track {slug}",
        audio_s3_key=f"audio/{slug}.mp3",
        latitude=56.8389,
        longitude=60.6057,
        moderation_status="published",
        is_published=True,
    )
    session.add(track)
    await session.commit()
    await session.refresh(track)
    return track


async def _create_published_route_with_stops(
    admin_client: AsyncClient,
    test_db_session: AsyncSession,
    track_slugs: list[str],
) -> dict:
    """Create a published route with track stops and linear dependencies (B depends on A, ...).
    Returns route dict.
    """
    route_resp = await admin_client.post(
        "/api/admin/routes",
        json={"title": "Published Route", "description": "Test"},
    )
    route_id = route_resp.json()["id"]

    prev_stop_id: int | None = None
    for slug in track_slugs:
        track = await _create_published_track(test_db_session, slug=slug)
        stop_resp = await admin_client.post(
            f"/api/admin/routes/{route_id}/stops",
            json={"stop_type": "track", "track_id": track.id},
        )
        assert stop_resp.status_code == 201
        stop_id = stop_resp.json()["id"]
        if prev_stop_id is not None:
            dep_resp = await admin_client.post(
                f"/api/admin/routes/{route_id}/stops/{stop_id}/dependencies",
                json={"depends_on_stop_id": prev_stop_id},
            )
            assert dep_resp.status_code == 201
        prev_stop_id = stop_id

    publish_resp = await admin_client.patch(
        f"/api/admin/routes/{route_id}",
        json={"is_published": True},
    )
    assert publish_resp.status_code == 200

    return route_resp.json()


@pytest.mark.routes
class TestListRoutes:
    """GET /api/routes — list published routes."""

    async def test_list_published_routes(self, admin_client: AsyncClient):
        pub_resp = await admin_client.post(
            "/api/admin/routes",
            json={"title": "Published One"},
        )
        await admin_client.patch(
            f"/api/admin/routes/{pub_resp.json()['id']}",
            json={"is_published": True},
        )

        unpub_resp = await admin_client.post(
            "/api/admin/routes",
            json={"title": "Unpublished One"},
        )

        response = await admin_client.get("/api/routes")
        assert response.status_code == 200, response.text
        routes = response.json()["routes"]
        titles = [r["title"] for r in routes]
        assert "Published One" in titles
        assert "Unpublished One" not in titles

    async def test_list_routes_empty(self, test_db_client: AsyncClient):
        response = await test_db_client.get("/api/routes")
        assert response.status_code == 200
        assert response.json()["routes"] == []


@pytest.mark.routes
class TestRouteDetail:
    """GET /api/routes/{slug} — route detail with stops."""

    async def test_get_route_detail(
        self,
        admin_client: AsyncClient,
        test_db_session: AsyncSession,
    ):
        route = await _create_published_route_with_stops(
            admin_client, test_db_session, ["detail-track-1", "detail-track-2"]
        )

        response = await admin_client.get(f"/api/routes/{route['slug']}")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["slug"] == route["slug"]
        assert data["title"] == "Published Route"
        assert len(data["stops"]) == 2
        assert data["stops"][0]["slug"] == "detail-track-1"
        assert data["stops"][1]["slug"] == "detail-track-2"

    async def test_get_route_not_found(self, test_db_client: AsyncClient):
        response = await test_db_client.get("/api/routes/nonexistent-slug")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_route_unpublished(self, admin_client: AsyncClient):
        create_resp = await admin_client.post(
            "/api/admin/routes",
            json={"title": "Never Published"},
        )
        slug = create_resp.json()["slug"]

        response = await admin_client.get(f"/api/routes/{slug}")
        assert response.status_code == 404

    async def test_route_detail_has_explicit_dependencies(
        self,
        admin_client: AsyncClient,
        test_db_session: AsyncSession,
    ):
        route = await _create_published_route_with_stops(
            admin_client, test_db_session, ["dep-track-1", "dep-track-2"]
        )

        response = await admin_client.get(f"/api/routes/{route['slug']}")
        assert response.status_code == 200
        stops = response.json()["stops"]
        assert len(stops) == 2
        assert stops[0]["depends_on"] == []
        assert stops[1]["depends_on"] == [stops[0]["id"]]
