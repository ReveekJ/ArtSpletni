"""
Integration tests for cycle prevention in route stop dependencies.

Covers:
- Direct cycle: A→B (auto), attempt B→A -> 400
- Self-dependency: stop→itself -> 400
- Three-node cycle: A, B, C (auto B→A, C→B), attempt A→C -> 400
- Valid non-cycle dependency -> 201
- Cross-route dependency rejected -> 400
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.audio_track import AudioTrack


async def _create_track(session: AsyncSession, slug: str) -> AudioTrack:
    track = AudioTrack(
        slug=slug,
        title=f"Track {slug}",
        audio_s3_key=f"audio/{slug}.mp3",
        latitude=0.0,
        longitude=0.0,
        moderation_status="published",
        is_published=True,
    )
    session.add(track)
    await session.commit()
    await session.refresh(track)
    return track


async def _create_route_with_stops(
    admin_client: AsyncClient,
    test_db_session: AsyncSession,
    track_slugs: list[str],
) -> dict:
    """Create a route with track stops and linear dependencies (B depends on A, C on B, ...).
    Returns route dict with 'id'.
    """
    route_resp = await admin_client.post(
        "/api/admin/routes",
        json={"title": "Cycle Test Route"},
    )
    route_id = route_resp.json()["id"]

    prev_stop_id: int | None = None
    for slug in track_slugs:
        track = await _create_track(test_db_session, slug=slug)
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

    return route_resp.json()


@pytest.mark.cycle
class TestCyclePrevention:
    """Cycle detection in stop dependencies."""

    async def test_cycle_prevention_direct(
        self,
        admin_client: AsyncClient,
        test_db_session: AsyncSession,
    ):
        route = await _create_route_with_stops(
            admin_client, test_db_session, ["cyc-a", "cyc-b"]
        )
        route_id = route["id"]

        stops_resp = await admin_client.get(f"/api/admin/routes/{route_id}/stops")
        stops = stops_resp.json()
        stop_a_id = stops[0]["id"]
        stop_b_id = stops[1]["id"]

        response = await admin_client.post(
            f"/api/admin/routes/{route_id}/stops/{stop_a_id}/dependencies",
            json={"depends_on_stop_id": stop_b_id},
        )

        assert response.status_code == 400
        assert "cycle" in response.json()["detail"].lower()

    async def test_cycle_prevention_self(
        self,
        admin_client: AsyncClient,
        test_db_session: AsyncSession,
    ):
        route = await _create_route_with_stops(
            admin_client, test_db_session, ["self-a"]
        )
        route_id = route["id"]

        stops_resp = await admin_client.get(f"/api/admin/routes/{route_id}/stops")
        stop_id = stops_resp.json()[0]["id"]

        response = await admin_client.post(
            f"/api/admin/routes/{route_id}/stops/{stop_id}/dependencies",
            json={"depends_on_stop_id": stop_id},
        )

        assert response.status_code == 400
        assert "itself" in response.json()["detail"].lower()

    async def test_cycle_prevention_three_node(
        self,
        admin_client: AsyncClient,
        test_db_session: AsyncSession,
    ):
        route = await _create_route_with_stops(
            admin_client, test_db_session, ["tri-a", "tri-b", "tri-c"]
        )
        route_id = route["id"]

        stops_resp = await admin_client.get(f"/api/admin/routes/{route_id}/stops")
        stops = stops_resp.json()
        stop_a_id = stops[0]["id"]
        stop_c_id = stops[2]["id"]

        response = await admin_client.post(
            f"/api/admin/routes/{route_id}/stops/{stop_a_id}/dependencies",
            json={"depends_on_stop_id": stop_c_id},
        )

        assert response.status_code == 400
        assert "cycle" in response.json()["detail"].lower()

    async def test_valid_dependency_allowed(
        self,
        admin_client: AsyncClient,
        test_db_session: AsyncSession,
    ):
        route = await _create_route_with_stops(
            admin_client, test_db_session, ["val-a", "val-b", "val-c"]
        )
        route_id = route["id"]

        stops_resp = await admin_client.get(f"/api/admin/routes/{route_id}/stops")
        stops = stops_resp.json()
        stop_a_id = stops[0]["id"]
        stop_c_id = stops[2]["id"]

        response = await admin_client.post(
            f"/api/admin/routes/{route_id}/stops/{stop_c_id}/dependencies",
            json={"depends_on_stop_id": stop_a_id},
        )

        assert response.status_code == 201

    async def test_dependency_cross_route_rejected(
        self,
        admin_client: AsyncClient,
        test_db_session: AsyncSession,
    ):
        route1 = await _create_route_with_stops(
            admin_client, test_db_session, ["cross-r1"]
        )
        route2 = await _create_route_with_stops(
            admin_client, test_db_session, ["cross-r2"]
        )

        stops1 = (
            await admin_client.get(f"/api/admin/routes/{route1['id']}/stops")
        ).json()
        stops2 = (
            await admin_client.get(f"/api/admin/routes/{route2['id']}/stops")
        ).json()

        stop1_id = stops1[0]["id"]
        stop2_id = stops2[0]["id"]

        response = await admin_client.post(
            f"/api/admin/routes/{route1['id']}/stops/{stop1_id}/dependencies",
            json={"depends_on_stop_id": stop2_id},
        )

        assert response.status_code == 400
        assert "not found in this route" in response.json()["detail"]

    async def test_duplicate_dependency_rejected(
        self,
        admin_client: AsyncClient,
        test_db_session: AsyncSession,
    ):
        route = await _create_route_with_stops(
            admin_client, test_db_session, ["dup-a", "dup-b", "dup-c"]
        )
        route_id = route["id"]

        stops_resp = await admin_client.get(f"/api/admin/routes/{route_id}/stops")
        stops = stops_resp.json()
        stop_a_id = stops[0]["id"]
        stop_c_id = stops[2]["id"]

        response = await admin_client.post(
            f"/api/admin/routes/{route_id}/stops/{stop_c_id}/dependencies",
            json={"depends_on_stop_id": stop_a_id},
        )
        assert response.status_code == 201

        response = await admin_client.post(
            f"/api/admin/routes/{route_id}/stops/{stop_c_id}/dependencies",
            json={"depends_on_stop_id": stop_a_id},
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
