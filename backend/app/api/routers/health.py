from fastapi import APIRouter

from app.core.db import engine

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    return {"status": "ok", "database": "connected" if await _db_ok() else "unavailable"}


async def _db_ok() -> bool:
    from sqlalchemy import text

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
