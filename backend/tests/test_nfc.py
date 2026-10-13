"""
Integration tests for NFC endpoints.

Covers:
- GET /api/nfc/track/{slug} — track in route without auth -> redirect to /login
- GET /api/nfc/track/{slug} — track in route with auth, deps not met -> 403
- GET /api/nfc/track/{slug} — track in route with auth, deps met -> redirect to /t/{slug}
- GET /api/nfc/track/{slug} — standalone track -> access grant cookie
- GET /api/nfc/checkpoint/{slug} — redirect to /c/{slug}
- GET /api/nfc/track/{slug} — not found / unpublished -> 404
- GET /api/nfc/{invalid_type}/{slug} -> 404
- Old URL /api/tracks/nfc/{slug} -> 404 (breaking change)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.audio_track import AudioTrack
from app.entities.checkpoint import Checkpoint


async def _create_track(
    session: AsyncSession,
    slug: str = "nfc-track",
    published: bool = True,
) -> AudioTrack:
    track = AudioTrack(
        slug=slug,
        title=f"Track {slug}",
        audio_s3_key=f"audio/{slug}.mp3",
        latitude=56.8389,
        longitude=60.6057,
        moderation_status="published" if published else "pending",
        is_published=published,
    )
    session.add(track)
    await session.commit()
    await session.refresh(track)
    return track


async def _create_checkpoint(
    session: AsyncSession,
    slug: str = "nfc-cp",
    published: bool = True,
) -> Checkpoint:
    cp = Checkpoint(
        slug=slug,
        title=f"CP {slug}",
        content_type="text",
        text_content="Hello",
        latitude=56.8389,
        longitude=60.6057,
        is_published=published,
    )
    session.add(cp)
    await session.commit()
    await session.refresh(cp)
    return cp


async def _create_route_with_track_stops(
    admin_client: AsyncClient,
    test_db_session: AsyncSession,
    track_slugs: list[str],
    publish_route: bool = True,
) -> dict:
    """Create a route with track stops. Returns route dict."""
    route_resp = await admin_client.post(
        "/api/admin/routes",
        json={"title": "NFC Test Route"},
    )
    route_id = route_resp.json()["id"]

    for slug in track_slugs:
        track = await _create_track(test_db_session, slug=slug)
        stop_resp = await admin_client.post(
            f"/api/admin/routes/{route_id}/stops",
            json={"stop_type": "track", "track_id": track.id},
        )
        assert stop_resp.status_code == 201

    if publish_route:
        await admin_client.patch(
            f"/api/admin/routes/{route_id}",
            json={"is_published": True},
        )

    return route_resp.json()


@pytest.mark.nfc
class TestNFCTrackInRoute:
    """NFC track that belongs to a route."""

    async def test_track_in_route_no_auth_redirects_to_login(
        self,
        admin_client: AsyncClient,
        test_db_session: AsyncSession,
        test_db_client: AsyncClient,
    ):
        route = await _create_route_with_track_stops(
            admin_client, test_db_session, ["nfc-no-auth"]
        )

        response = await test_db_client.get("/api/nfc/track/nfc-no-auth")

        assert response.status_code == 302
        location = response.headers["location"]
        assert location.startswith("/login?next=/api/nfc/track/nfc-no-auth")

    async def test_track_in_route_deps_not_met_returns_403(
        self,
        admin_client: AsyncClient,
        test_db_session: AsyncSession,
        authenticated_client: AsyncClient,
    ):
        route = await _create_route_with_track_stops(
            admin_client, test_db_session, ["nfc-dep-a", "nfc-dep-b"]
        )

        response = await authenticated_client.get("/api/nfc/track/nfc-dep-b")

        assert response.status_code == 403
        assert "Previous stops" in response.json()["detail"]

    async def test_track_in_route_deps_met_redirects_to_track(
        self,
        admin_client: AsyncClient,
        test_db_session: AsyncSession,
        authenticated_client: AsyncClient,
    ):
        route = await _create_route_with_track_stops(
            admin_client, test_db_session, ["nfc-ok-a", "nfc-ok-b"]
        )

        scan_resp = await authenticated_client.get("/api/nfc/track/nfc-ok-a")
        assert scan_resp.status_code == 302
        assert scan_resp.headers["location"] == "/t/nfc-ok-a"

        response = await authenticated_client.get("/api/nfc/track/nfc-ok-b")
        assert response.status_code == 302
        assert response.headers["location"] == "/t/nfc-ok-b"


@pytest.mark.nfc
class TestNFCStandaloneTrack:
    """NFC track that does NOT belong to any route — old access grant behavior."""

    async def test_standalone_track_sets_access_cookie(
        self,
        test_db_session: AsyncSession,
        test_db_client: AsyncClient,
    ):
        await _create_track(test_db_session, slug="standalone-track")

        response = await test_db_client.get("/api/nfc/track/standalone-track")

        assert response.status_code == 302
        assert response.headers["location"] == "/t/standalone-track"
        set_cookie = response.headers.get("set-cookie", "")
        assert "spletni_track_access" in set_cookie

    async def test_standalone_track_cookie_grants_access(
        self,
        test_db_session: AsyncSession,
        test_db_client: AsyncClient,
    ):
        await _create_track(test_db_session, slug="grant-access-track")

        nfc_resp = await test_db_client.get("/api/nfc/track/grant-access-track")
        assert nfc_resp.status_code == 302

        response = await test_db_client.get("/api/tracks/grant-access-track")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["slug"] == "grant-access-track"
        assert data["title"] == "Track grant-access-track"


@pytest.mark.nfc
class TestNFCCheckpoint:
    """NFC checkpoint redirect."""

    async def test_nfc_checkpoint_in_route_redirects(
        self,
        admin_client: AsyncClient,
        test_db_session: AsyncSession,
        authenticated_client: AsyncClient,
    ):
        cp = await _create_checkpoint(test_db_session, slug="nfc-cp-route")

        route_resp = await admin_client.post(
            "/api/admin/routes",
            json={"title": "CP Route"},
        )
        route_id = route_resp.json()["id"]
        await admin_client.post(
            f"/api/admin/routes/{route_id}/stops",
            json={"stop_type": "checkpoint", "checkpoint_id": cp.id},
        )
        await admin_client.patch(
            f"/api/admin/routes/{route_id}",
            json={"is_published": True},
        )

        response = await authenticated_client.get("/api/nfc/checkpoint/nfc-cp-route")
        assert response.status_code == 302
        assert response.headers["location"] == "/c/nfc-cp-route"

    async def test_nfc_checkpoint_standalone_redirects(
        self,
        test_db_session: AsyncSession,
        test_db_client: AsyncClient,
    ):
        await _create_checkpoint(test_db_session, slug="standalone-cp")

        response = await test_db_client.get("/api/nfc/checkpoint/standalone-cp")
        assert response.status_code == 302
        assert response.headers["location"] == "/c/standalone-cp"


@pytest.mark.nfc
class TestNFCErrorCases:
    """NFC error / edge cases."""

    async def test_nfc_track_not_found(self, test_db_client: AsyncClient):
        response = await test_db_client.get("/api/nfc/track/nonexistent")
        assert response.status_code == 404

    async def test_nfc_track_unpublished(
        self,
        test_db_session: AsyncSession,
        test_db_client: AsyncClient,
    ):
        await _create_track(test_db_session, slug="unpub-nfc", published=False)

        response = await test_db_client.get("/api/nfc/track/unpub-nfc")
        assert response.status_code == 404

    async def test_nfc_invalid_stop_type(self, test_db_client: AsyncClient):
        response = await test_db_client.get("/api/nfc/invalid/some-slug")
        assert response.status_code == 404

    async def test_old_track_nfc_url_returns_404(self, test_db_client: AsyncClient):
        response = await test_db_client.get("/api/tracks/nfc/some-slug")
        assert response.status_code == 404
