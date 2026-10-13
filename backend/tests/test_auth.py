"""
Integration tests for authentication endpoints.

Covers:
- POST /api/auth/register (success, duplicate, invalid email, short password)
- POST /api/auth/login (success, invalid credentials, nonexistent user)
- GET /api/auth/me (authenticated, unauthenticated)
- DELETE /api/auth/session (logout)
- GET /api/auth/yandex (redirect URL, not configured)
- GET /api/auth/yandex/callback (success, existing user)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.auth
class TestAuthRegister:
    """Tests for POST /api/auth/register."""

    async def test_register_success(self, test_db_client: AsyncClient):
        response = await test_db_client.post(
            "/api/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "password123",
                "display_name": "New User",
            },
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["display_name"] == "New User"
        assert data["is_admin"] is False
        assert "id" in data

    async def test_register_duplicate_email(self, test_db_client: AsyncClient):
        payload = {
            "email": "dup@test.com",
            "password": "password123",
            "display_name": "Dup User",
        }
        first = await test_db_client.post("/api/auth/register", json=payload)
        assert first.status_code == 201

        second = await test_db_client.post("/api/auth/register", json=payload)
        assert second.status_code == 409
        assert "already registered" in second.json()["detail"]

    async def test_register_invalid_email(self, test_db_client: AsyncClient):
        response = await test_db_client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
                "display_name": "Bad Email",
            },
        )
        assert response.status_code == 422

    async def test_register_short_password(self, test_db_client: AsyncClient):
        response = await test_db_client.post(
            "/api/auth/register",
            json={
                "email": "shortpw@test.com",
                "password": "12345",
                "display_name": "Short PW",
            },
        )
        assert response.status_code == 422


@pytest.mark.auth
class TestAuthLogin:
    """Tests for POST /api/auth/login."""

    async def test_login_success(self, test_db_client: AsyncClient):
        await test_db_client.post(
            "/api/auth/register",
            json={
                "email": "loginuser@test.com",
                "password": "password123",
                "display_name": "Login User",
            },
        )
        response = await test_db_client.post(
            "/api/auth/login",
            json={"email": "loginuser@test.com", "password": "password123"},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["email"] == "loginuser@test.com"
        assert data["display_name"] == "Login User"

    async def test_login_invalid_credentials(self, test_db_client: AsyncClient):
        await test_db_client.post(
            "/api/auth/register",
            json={
                "email": "badpw@test.com",
                "password": "password123",
                "display_name": "Bad PW",
            },
        )
        response = await test_db_client.post(
            "/api/auth/login",
            json={"email": "badpw@test.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    async def test_login_nonexistent_user(self, test_db_client: AsyncClient):
        response = await test_db_client.post(
            "/api/auth/login",
            json={"email": "ghost@test.com", "password": "password123"},
        )
        assert response.status_code == 401


@pytest.mark.auth
class TestAuthMe:
    """Tests for GET /api/auth/me."""

    async def test_me_authenticated(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get("/api/auth/me")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["email"] == "user@test.com"
        assert data["display_name"] == "Test User"

    async def test_me_unauthenticated(self, test_db_client: AsyncClient):
        response = await test_db_client.get("/api/auth/me")
        assert response.status_code == 200
        assert response.json() is None


@pytest.mark.auth
class TestAuthLogout:
    """Tests for DELETE /api/auth/session."""

    async def test_logout(self, authenticated_client: AsyncClient):
        response = await authenticated_client.delete("/api/auth/session")
        assert response.status_code == 200
        assert response.json()["authenticated"] is False

        me_response = await authenticated_client.get("/api/auth/me")
        assert me_response.status_code == 200
        assert me_response.json() is None


@pytest.mark.auth
class TestYandexOAuth:
    """Tests for Yandex OAuth endpoints."""

    async def test_yandex_redirect(self, test_db_client: AsyncClient):
        response = await test_db_client.get("/api/auth/yandex")
        assert response.status_code == 200, response.text
        data = response.json()
        assert "auth_url" in data
        assert "oauth.yandex.ru/authorize" in data["auth_url"]
        assert "test-yandex-id" in data["auth_url"]

    async def test_yandex_not_configured(self, test_db_client: AsyncClient):
        from app.core.config import get_settings

        original = get_settings().yandex_client_id
        get_settings().yandex_client_id = ""
        try:
            response = await test_db_client.get("/api/auth/yandex")
            assert response.status_code == 503
            assert "not configured" in response.json()["detail"].lower()
        finally:
            get_settings().yandex_client_id = original

    async def test_yandex_callback_success(self, test_db_client: AsyncClient):
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"access_token": "fake-yandex-token"}

        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            "id": "yandex-123",
            "default_email": "yandexuser@yandex.ru",
            "real_name": "Yandex User",
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_token_response
        mock_client.get.return_value = mock_user_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            response = await test_db_client.get(
                "/api/auth/yandex/callback?code=test-code"
            )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["email"] == "yandexuser@yandex.ru"

        me_response = await test_db_client.get("/api/auth/me")
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "yandexuser@yandex.ru"

    async def test_yandex_callback_existing_user(self, test_db_client: AsyncClient):
        await test_db_client.post(
            "/api/auth/register",
            json={
                "email": "existing@yandex.ru",
                "password": "password123",
                "display_name": "Pre Existing",
            },
        )

        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"access_token": "fake-token-2"}

        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            "id": "yandex-456",
            "default_email": "existing@yandex.ru",
            "real_name": "Pre Existing",
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_token_response
        mock_client.get.return_value = mock_user_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            response = await test_db_client.get(
                "/api/auth/yandex/callback?code=test-code-2"
            )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["email"] == "existing@yandex.ru"
