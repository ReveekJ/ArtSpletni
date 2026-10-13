"""
Database fixtures for pytest.

Uses testcontainers to provide a real PostgreSQL instance.
Container is shared across all tests in the session for performance.
Each test gets transaction isolation via savepoints.
"""

import logging
import os
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.db import get_session
from app.main import app

logging.getLogger("alembic").setLevel(logging.WARNING)
logging.getLogger("alembic.runtime.migration").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("asyncpg").setLevel(logging.WARNING)
logging.getLogger("testcontainers").setLevel(logging.WARNING)


def apply_alembic_migrations(db_url: str) -> None:
    """Apply Alembic migrations to the test database.

    alembic/env.py reads get_settings().database_url and creates an async
    engine from it, so we patch the cached Settings to point at the
    container's asyncpg URL before running migrations.
    """
    from alembic import command
    from alembic.config import Config as AlembicConfig

    if "postgresql+psycopg2://" in db_url:
        async_db_url = db_url.replace(
            "postgresql+psycopg2://", "postgresql+asyncpg://", 1
        )
    elif db_url.startswith("postgresql://"):
        async_db_url = db_url.replace(
            "postgresql://", "postgresql+asyncpg://", 1
        )
    else:
        async_db_url = db_url

    from app.core.config import get_settings

    settings = get_settings()
    original_db_url = settings.database_url
    settings.database_url = async_db_url

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alembic_ini_path = os.path.join(project_root, "alembic.ini")
    alembic_cfg = AlembicConfig(alembic_ini_path)

    try:
        command.upgrade(alembic_cfg, "head")
    finally:
        settings.database_url = original_db_url


@pytest.fixture(scope="session")
def postgres_container():
    """
    Real PostgreSQL container for tests.
    Uses testcontainers to spin up a real PostgreSQL instance.
    Container is shared across all tests in the session.
    """
    try:
        from testcontainers.postgres import PostgresContainer

        container = PostgresContainer("postgres:16-alpine")
        container.start()

        postgresql_url = container.get_connection_url()
        apply_alembic_migrations(postgresql_url)

        yield container

        container.stop()
    except ImportError:
        pytest.skip(
            "testcontainers[postgres] not installed. "
            "Install with: uv add --dev 'testcontainers[postgres]'"
        )
    except Exception as exc:
        import traceback

        traceback.print_exc()
        pytest.skip(
            f"Failed to start PostgreSQL container: {exc}. "
            "Make sure Docker is running."
        )


@pytest.fixture(scope="function")
async def test_db_engine(postgres_container):
    """Create test async engine from the container's connection URL."""
    postgresql_url = postgres_container.get_connection_url()

    if postgresql_url.startswith("postgresql://"):
        db_url = postgresql_url.replace(
            "postgresql://", "postgresql+asyncpg://", 1
        )
    elif "postgresql+psycopg2://" in postgresql_url:
        db_url = postgresql_url.replace(
            "postgresql+psycopg2://", "postgresql+asyncpg://", 1
        )
    else:
        db_url = postgresql_url

    engine = create_async_engine(db_url, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session for each test.
    Uses savepoint isolation so commits inside services are visible
    to the test client but rolled back at the end.

    join_transaction_mode="create_savepoint" is load-bearing:
    SQLAlchemy 2.0 Session.commit() commits the entire transaction stack.
    This mode opens a fresh SAVEPOINT after each commit/rollback, so the
    outer transaction is never closed until the explicit rollback below.
    """
    async with test_db_engine.connect() as connection:
        await connection.begin()
        await connection.begin_nested()

        async_session_maker = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        async with async_session_maker() as session:
            yield session

        try:
            await connection.rollback()
        except Exception:
            pass


@pytest.fixture(scope="function")
async def test_db_client(
    test_db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test HTTP client for the FastAPI application.
    Overrides get_session dependency with the test session.
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
        yield client

    app.dependency_overrides.clear()
