"""
Authentication fixtures for pytest.

Provides admin_client, authenticated_client, and second_user_client.
All fixtures use the real FastAPI test client (test_db_client) and
authenticate via the real API endpoints.
"""

from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.main import app


@pytest.fixture(scope="function")
async def admin_client(
    test_db_client: AsyncClient,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Authenticate as admin via POST /api/admin/session.
    Returns the test client with admin session cookie set.
    """
    response = await test_db_client.post(
        "/api/admin/session",
        json={"username": "admin", "password": "admin-spletni"},
    )
    assert response.status_code == 200, response.text
    yield test_db_client


@pytest.fixture(scope="function")
async def authenticated_client(
    test_db_client: AsyncClient,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Register and authenticate a test user via the real API.
    Returns the test client with session cookie set.
    """
    response = await test_db_client.post(
        "/api/auth/register",
        json={
            "email": "user@test.com",
            "password": "password123",
            "display_name": "Test User",
        },
    )
    assert response.status_code == 201, response.text
    yield test_db_client


@pytest.fixture(scope="function")
async def second_user_client(
    test_db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Register and authenticate a second test user.
    Uses a fresh AsyncClient bound to the same test session.
    """
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield test_db_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        follow_redirects=False,
    ) as client:
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "user2@test.com",
                "password": "password123",
                "display_name": "Test User 2",
            },
        )
        assert response.status_code == 201, response.text
        yield client

    app.dependency_overrides.clear()
