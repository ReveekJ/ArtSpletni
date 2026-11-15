from litestar import Controller, get
from litestar.di import NamedDependency
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.lib.schema import CamelizedBaseStruct


class HealthStatus(CamelizedBaseStruct):
    status: str


class HealthController(Controller):
    path = "/api/health"
    tags = ["System"]

    @get("/", summary="Health check", description="Liveness probe that also pings the database.")
    async def health(self, db_session: NamedDependency[AsyncSession]) -> HealthStatus:
        await db_session.execute(text("SELECT 1"))
        return HealthStatus(status="ok")
