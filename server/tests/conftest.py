import os
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack

import pytest
from advanced_alchemy.base import UUIDv7AuditBase
from litestar import Litestar
from litestar.testing import AsyncTestClient
from litestar_email import InMemoryBackend
from pytest_databases.docker.postgres import PostgresService
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.pool import NullPool

from tests.fakes import (
    FakeGossipWriter,
    FakeLinkChecker,
    FakeNearbySource,
    FakeObjectStorage,
    FakeTranslationProvider,
    GossipFakes,
)

pytest_plugins = ["pytest_databases.docker.postgres"]

ADMIN_PASSWORD = "admin-password-1"
PLAYER_PASSWORD = "player-password-1"

Client = AsyncTestClient[Litestar]


@pytest.fixture(scope="session")
def database_url(request: pytest.FixtureRequest) -> str:
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        return explicit
    service: PostgresService = request.getfixturevalue("postgres_service")
    return f"postgresql+asyncpg://{service.user}:{service.password}@{service.host}:{service.port}/{service.database}"


@pytest.fixture(scope="session")
def configured_env(database_url: str) -> None:
    os.environ.update(
        {
            "DATABASE_URL": database_url,
            "SECRET_KEY": "test-secret-key-test-secret-key-test-secret",
            "PUBLIC_BASE_URL": "http://app.test",
            "SESSION_COOKIE_SECURE": "false",
            "MAIL_FALLBACK_BACKEND": "memory",
            "S3__ENDPOINT": "http://s3.test",
            "S3__PUBLIC_ENDPOINT": "http://s3.test",
            "S3__ACCESS_KEY": "test",
            "S3__SECRET_KEY": "test",
            "S3__BUCKET": "test",
            "LLM__BASE_URL": "http://llm.test/v1",
            "LLM__MODEL": "test-model",
            "YANDEX__CLIENT_ID": "yandex-client",
            "YANDEX__CLIENT_SECRET": "yandex-secret",
            "YANDEX__REDIRECT_URI": "http://app.test/api/auth/yandex/callback",
        }
    )
    from app.config import alchemy_config
    from app.lib.settings import get_settings

    get_settings.cache_clear()
    alchemy_config.cache_clear()
    alchemy_config().engine_config.poolclass = NullPool


@pytest.fixture(scope="session")
async def app(configured_env: None) -> Litestar:
    import app.db.models  # noqa: F401
    from app.asgi import create_app
    from app.config import alchemy_config

    application = create_app()
    async with alchemy_config().get_engine().begin() as connection:
        await connection.run_sync(UUIDv7AuditBase.metadata.drop_all)
        await connection.run_sync(UUIDv7AuditBase.metadata.create_all)
    return application


@pytest.fixture(autouse=True)
async def clean_database(app: Litestar) -> AsyncIterator[None]:
    from app.config import alchemy_config

    yield
    tables = ", ".join(f'"{table.name}"' for table in UUIDv7AuditBase.metadata.sorted_tables)
    async with alchemy_config().get_engine().begin() as connection:
        await connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    InMemoryBackend.clear()


@pytest.fixture(autouse=True)
def storage(monkeypatch: pytest.MonkeyPatch) -> FakeObjectStorage:
    fake = FakeObjectStorage()
    monkeypatch.setattr("app.domain.media.deps.object_storage", lambda: fake)
    return fake


@pytest.fixture(autouse=True)
def translator(monkeypatch: pytest.MonkeyPatch) -> FakeTranslationProvider:
    fake = FakeTranslationProvider()
    monkeypatch.setattr("app.domain.i18n.deps.translation_provider", lambda: fake)
    return fake


@pytest.fixture(autouse=True)
def gossip(monkeypatch: pytest.MonkeyPatch) -> GossipFakes:
    fakes = GossipFakes(nearby=FakeNearbySource(), writer=FakeGossipWriter(), links=FakeLinkChecker())
    monkeypatch.setattr("app.domain.gossip.deps.nearby_source", lambda: fakes.nearby)
    monkeypatch.setattr("app.domain.gossip.deps.gossip_writer", lambda: fakes.writer)
    monkeypatch.setattr("app.domain.gossip.deps.link_checker", lambda: fakes.links)
    return fakes


@pytest.fixture
async def client(app: Litestar) -> AsyncIterator[Client]:
    async with AsyncTestClient(app=app, base_url="http://app.test") as test_client:
        yield test_client


@pytest.fixture
async def player(app: Litestar) -> AsyncIterator[Client]:
    async with AsyncTestClient(app=app, base_url="http://app.test") as test_client:
        yield test_client


@pytest.fixture
async def other_player(app: Litestar) -> AsyncIterator[Client]:
    async with AsyncTestClient(app=app, base_url="http://app.test") as test_client:
        yield test_client


@pytest.fixture
async def app_clients(app: Litestar) -> AsyncIterator[list[Client]]:
    async with AsyncExitStack() as stack:
        clients = [
            await stack.enter_async_context(AsyncTestClient(app=app, base_url="http://app.test"))
            for _ in range(4)
        ]
        yield clients


@pytest.fixture
async def db_session(app: Litestar) -> AsyncIterator[AsyncSession]:
    from app.config import alchemy_config

    async with alchemy_config().get_session() as session:
        yield session


async def register(client: Client, email: str, password: str = PLAYER_PASSWORD) -> dict[str, str]:
    response = await client.post("/api/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201, response.text
    body: dict[str, str] = response.json()
    return body


@pytest.fixture
async def admin_client(client: Client) -> Client:
    from app.domain.users.cli import _create_admin

    await _create_admin("admin@spletni.test", ADMIN_PASSWORD)
    response = await client.post(
        "/api/auth/login", json={"email": "admin@spletni.test", "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, response.text
    return client
