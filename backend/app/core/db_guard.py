import asyncio
import sys

from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import engine

TEST_DB_PREFIXES = ("test_", "test-")


def is_test_database(url: str) -> bool:
    name = url.rsplit("/", 1)[-1].split("?")[0]
    return name.startswith(TEST_DB_PREFIXES)


async def check_database_name() -> None:
    settings = get_settings()
    if not settings.db_guard_enabled:
        print("Database guard disabled via DB_GUARD_ENABLED, skipping check")
        return
    if not is_test_database(settings.database_url):
        print(
            f"REFUSING TO START: database '{settings.database_url}' is not a test database "
            f"(must start with 'test_' or 'test-')",
            file=sys.stderr,
        )
        raise SystemExit(1)
    async with engine.connect() as conn:
        db_name = (await conn.execute(text("SELECT current_database()"))).scalar_one()
    if not str(db_name).startswith(TEST_DB_PREFIXES):
        print(
            f"REFUSING TO START: connected database '{db_name}' is not a test database",
            file=sys.stderr,
        )
        raise SystemExit(1)


async def main() -> None:
    await check_database_name()
    print("Database check passed")


if __name__ == "__main__":
    asyncio.run(main())
