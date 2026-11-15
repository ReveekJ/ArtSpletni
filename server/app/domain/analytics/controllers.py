from typing import Annotated
from uuid import UUID

from litestar import Controller, get, post
from litestar.di import NamedDependency, Provide
from litestar.params import FromPath, JSONBody, QueryParameter
from litestar.status_codes import HTTP_204_NO_CONTENT
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import rate_limit
from app.domain.analytics.repository import AnalyticsRepository
from app.domain.analytics.schemas import (
    OverviewOut,
    PlaybackActivityOut,
    PlaybackInput,
    PointActivityOut,
    RouteFunnelOut,
)
from app.domain.analytics.services import AnalyticsService, PlaybackService
from app.domain.auth.guards import requires_actor, requires_admin
from app.domain.points.repositories import PointRepository, UnlockRepository
from app.domain.routes.repositories import RouteRepository
from app.lib.request import AppRequest, require_user
from app.lib.settings import get_settings

PLAYBACK_RATE_LIMIT = rate_limit("playback", "minute", 120)
Days = Annotated[int, QueryParameter(name="days", ge=1, le=365)]


async def provide_playback_service(db_session: NamedDependency[AsyncSession]) -> PlaybackService:
    return PlaybackService(
        db_session, UnlockRepository(session=db_session), PointRepository(session=db_session)
    )


async def provide_analytics_service(
    db_session: NamedDependency[AsyncSession], language: NamedDependency[str]
) -> AnalyticsService:
    return AnalyticsService(
        AnalyticsRepository(db_session),
        PointRepository(session=db_session),
        RouteRepository(session=db_session),
        language,
        get_settings().default_language,
    )


class PlaybackController(Controller):
    path = "/api/analytics"
    tags = ["Analytics"]
    guards = [requires_actor]
    dependencies = {"playback_service": Provide(provide_playback_service)}

    @post(
        "/playback",
        summary="Report playback",
        description="Report audio/video progress for statistics; does not affect route progress.",
        status_code=HTTP_204_NO_CONTENT,
        middleware=[PLAYBACK_RATE_LIMIT.middleware],
    )
    async def report(
        self,
        request: AppRequest,
        data: JSONBody[PlaybackInput],
        playback_service: NamedDependency[PlaybackService],
    ) -> None:
        await playback_service.record(require_user(request), data)


class AdminAnalyticsController(Controller):
    path = "/api/admin/analytics"
    tags = ["Admin: Analytics"]
    guards = [requires_admin]
    dependencies = {"analytics_service": Provide(provide_analytics_service)}

    @get("/overview", summary="Overview", description="Key counters for the last N days.")
    async def overview(
        self, analytics_service: NamedDependency[AnalyticsService], days: Days = 30
    ) -> OverviewOut:
        return await analytics_service.overview(days)

    @get("/points", summary="Point activity", description="Successful scans and unique visitors per point.")
    async def points(
        self, analytics_service: NamedDependency[AnalyticsService], days: Days = 30
    ) -> list[PointActivityOut]:
        return await analytics_service.points(days)

    @get(
        "/routes/{route_id:uuid}/funnel",
        summary="Route funnel",
        description="Runs started, completed and visits per stop.",
    )
    async def funnel(
        self, route_id: FromPath[UUID], analytics_service: NamedDependency[AnalyticsService]
    ) -> RouteFunnelOut:
        return await analytics_service.route_funnel(route_id)

    @get("/playback", summary="Playback", description="Listening and viewing completion per media asset.")
    async def playback(
        self, analytics_service: NamedDependency[AnalyticsService], days: Days = 30
    ) -> list[PlaybackActivityOut]:
        return await analytics_service.playback(days)
