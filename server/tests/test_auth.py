from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from litestar import Litestar
from litestar_email import InMemoryBackend
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, UserKind
from app.domain.auth.merge import AccountMergeService
from app.domain.auth.services import AuthService
from app.domain.users.services import UserService
from app.lib.http import HTTP_CLIENT_STATE_KEY
from tests.conftest import PLAYER_PASSWORD, Client, register

pytestmark = pytest.mark.auth


async def test_register_starts_session(client: Client) -> None:
    profile = await register(client, "Player@Example.com")
    assert profile["email"] == "player@example.com"
    assert profile["kind"] == "registered"

    session = (await client.get("/api/auth/session")).json()
    assert session["user"]["id"] == profile["id"]


async def test_register_rejects_duplicate_email(client: Client) -> None:
    await register(client, "dup@example.com")
    response = await client.post(
        "/api/auth/register", json={"email": "DUP@example.com", "password": PLAYER_PASSWORD}
    )
    assert response.status_code == 409
    assert response.json()["code"] == "email_taken"


async def test_register_validates_password_length(client: Client) -> None:
    response = await client.post("/api/auth/register", json={"email": "a@example.com", "password": "short"})
    assert response.status_code == 400


async def test_login_logout_cycle(client: Client) -> None:
    await register(client, "cycle@example.com")
    await client.post("/api/auth/logout")
    assert (await client.get("/api/auth/session")).json() == {"user": None}

    bad = await client.post("/api/auth/login", json={"email": "cycle@example.com", "password": "wrong-pass"})
    assert bad.status_code == 401
    assert bad.json()["code"] == "invalid_credentials"

    good = await client.post(
        "/api/auth/login", json={"email": "cycle@example.com", "password": PLAYER_PASSWORD}
    )
    assert good.status_code == 200
    assert (await client.get("/api/auth/session")).json()["user"]["email"] == "cycle@example.com"


async def test_login_unknown_email_is_unauthorized(client: Client) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": "nobody@example.com", "password": "whatever1"}
    )
    assert response.status_code == 401


async def test_password_reset_flow(client: Client) -> None:
    await register(client, "reset@example.com")
    await client.post("/api/auth/logout")

    response = await client.post("/api/auth/password-reset/request", json={"email": "reset@example.com"})
    assert response.status_code == 202
    assert len(InMemoryBackend.outbox) == 1
    body = InMemoryBackend.outbox[0].body
    token = parse_qs(urlparse(body.split()[-1]).query)["token"][0]

    confirm = await client.post(
        "/api/auth/password-reset/confirm", json={"token": token, "password": "brand-new-password"}
    )
    assert confirm.status_code == 204
    reused = await client.post(
        "/api/auth/password-reset/confirm", json={"token": token, "password": "another-password"}
    )
    assert reused.status_code == 400
    assert reused.json()["code"] == "invalid_reset_token"

    login = await client.post(
        "/api/auth/login", json={"email": "reset@example.com", "password": "brand-new-password"}
    )
    assert login.status_code == 200


async def test_password_reset_unknown_email_sends_nothing(client: Client) -> None:
    response = await client.post("/api/auth/password-reset/request", json={"email": "ghost@example.com"})
    assert response.status_code == 202
    assert InMemoryBackend.outbox == []


async def test_admin_routes_are_guarded(client: Client) -> None:
    payload = {"kind": "image", "contentType": "image/png", "sizeBytes": 10}
    assert (await client.post("/api/admin/media/uploads", json=payload)).status_code == 401
    await register(client, "player@example.com")
    assert (await client.post("/api/admin/media/uploads", json=payload)).status_code == 403


async def test_register_upgrades_guest_in_place(db_session: AsyncSession) -> None:
    users = UserService(session=db_session)
    guest = await users.create_guest()
    service = AuthService(users, AccountMergeService(users, ()))

    user = await service.register("guest@example.com", PLAYER_PASSWORD, "Guest", guest)

    assert user.id == guest.id
    assert user.kind is UserKind.REGISTERED


async def test_login_absorbs_guest(db_session: AsyncSession) -> None:
    users = UserService(session=db_session)
    service = AuthService(users, AccountMergeService(users, ()))
    account = await service.register("owner@example.com", PLAYER_PASSWORD, None, None)
    guest = await users.create_guest()

    logged_in = await service.authenticate("owner@example.com", PLAYER_PASSWORD, guest)

    assert logged_in.id == account.id
    assert await users.get_one_or_none(id=guest.id) is None


def _mock_yandex(app: Litestar, profile: dict[str, str]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "oauth.yandex.ru":
            assert b"code_verifier=" in request.content
            return httpx.Response(200, json={"access_token": "token"})
        return httpx.Response(200, json=profile)

    app.state[HTTP_CLIENT_STATE_KEY] = httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_yandex_login_creates_account(app: Litestar, client: Client) -> None:
    _mock_yandex(app, {"id": "ya-1", "default_email": "Ya@Yandex.ru", "display_name": "Ya"})

    start = await client.get("/api/auth/yandex/login", params={"next": "/routes"}, follow_redirects=False)
    assert start.status_code == 302
    query = parse_qs(urlparse(start.headers["location"]).query)
    assert query["code_challenge_method"] == ["S256"]

    callback = await client.get(
        "/api/auth/yandex/callback",
        params={"code": "abc", "state": query["state"][0]},
        follow_redirects=False,
    )
    assert callback.status_code == 302
    assert callback.headers["location"] == "http://app.test/routes"
    user = (await client.get("/api/auth/session")).json()["user"]
    assert user["email"] == "ya@yandex.ru"


async def test_yandex_callback_rejects_wrong_state(app: Litestar, client: Client) -> None:
    _mock_yandex(app, {"id": "ya-2"})
    await client.get("/api/auth/yandex/login", follow_redirects=False)

    callback = await client.get(
        "/api/auth/yandex/callback", params={"code": "abc", "state": "forged"}, follow_redirects=False
    )

    assert callback.headers["location"] == "http://app.test/login?error=oauth_failed"
    assert (await client.get("/api/auth/session")).json() == {"user": None}


async def test_yandex_links_existing_email_account(
    app: Litestar, client: Client, db_session: AsyncSession
) -> None:
    profile = await register(client, "linked@example.com")
    await client.post("/api/auth/logout")
    _mock_yandex(app, {"id": "ya-3", "default_email": "linked@example.com"})

    start = await client.get("/api/auth/yandex/login", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    await client.get(
        "/api/auth/yandex/callback", params={"code": "c", "state": state}, follow_redirects=False
    )

    user = await db_session.get(User, profile["id"])
    assert user is not None
    assert user.yandex_id == "ya-3"
