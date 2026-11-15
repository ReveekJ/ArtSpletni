from datetime import timedelta
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PlaybackEvent, Point, User
from app.domain.analytics.repository import AnalyticsRepository
from app.domain.analytics.schemas import (
    FunnelStopOut,
    OverviewOut,
    PlaybackActivityOut,
    PlaybackInput,
    PointActivityOut,
    RouteFunnelOut,
)
from app.domain.points.repositories import PointRepository, UnlockRepository
from app.domain.routes.repositories import RouteRepository
from app.domain.runs.services import utcnow
from app.lib.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.lib.i18n import resolve_text

COMPLETION_RATIO = 0.95


class PlaybackService:
    def __init__(self, session: AsyncSession, unlocks: UnlockRepository, points: PointRepository) -> None:
        self._session = session
        self._unlocks = unlocks
        self._points = points

    async def record(self, user: User, data: PlaybackInput) -> None:
        if await self._unlocks.get_one_or_none(user_id=user.id, point_id=data.point_id) is None:
            raise ForbiddenError("Point is locked", code="point_locked")
        point = await self._points.get_one_or_none(id=data.point_id)
        asset_ids = {
            asset_id
            for block in (point.blocks if point else [])
            for asset_id in [block.asset_id, *(variant.asset_id for variant in block.media_variants)]
        }
        if data.asset_id not in asset_ids:
            raise BadRequestError("Media does not belong to this point", code="media_not_in_point")
        position = min(data.position_seconds, data.duration_seconds)
        completed = data.duration_seconds > 0 and position >= data.duration_seconds * COMPLETION_RATIO
        statement = insert(PlaybackEvent).values(
            user_id=user.id,
            point_id=data.point_id,
            asset_id=data.asset_id,
            session_key=data.session_key,
            position_seconds=position,
            duration_seconds=data.duration_seconds,
            completed=completed,
        )
        await self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[PlaybackEvent.session_key],
                set_={
                    "position_seconds": statement.excluded.position_seconds,
                    "duration_seconds": statement.excluded.duration_seconds,
                    "completed": PlaybackEvent.completed | statement.excluded.completed,
                    "updated_at": utcnow(),
                },
                where=(PlaybackEvent.user_id == user.id)
                & (PlaybackEvent.position_seconds <= statement.excluded.position_seconds),
            )
        )


class AnalyticsService:
    def __init__(
        self,
        repository: AnalyticsRepository,
        points: PointRepository,
        routes: RouteRepository,
        language: str,
        fallback: str,
    ) -> None:
        self._repository = repository
        self._points = points
        self._routes = routes
        self._language = language
        self._fallback = fallback

    async def overview(self, days: int) -> OverviewOut:
        data = await self._repository.overview(utcnow() - timedelta(days=days))
        return OverviewOut(
            days=days,
            scans=data.scans,
            failed_scans=data.failed_scans,
            active_users=data.active_users,
            new_accounts=data.new_accounts,
            runs_started=data.runs_started,
            runs_completed=data.runs_completed,
            offers_granted=data.offers_granted,
            offers_redeemed=data.offers_redeemed,
        )

    async def points(self, days: int) -> list[PointActivityOut]:
        activity = await self._repository.point_activity(utcnow() - timedelta(days=days))
        titles = await self._point_titles({item.point_id for item in activity})
        return [
            PointActivityOut(
                point_id=item.point_id,
                title=titles.get(item.point_id, ""),
                scans=item.scans,
                unique_users=item.unique_users,
            )
            for item in activity
        ]

    async def route_funnel(self, route_id: UUID) -> RouteFunnelOut:
        route = await self._routes.get_one_or_none(id=route_id)
        if route is None:
            raise NotFoundError("Route not found", code="route_not_found")
        started, completed, visits = await self._repository.route_funnel(route_id)
        titles = await self._point_titles({stop.point_id for stop in route.stops})
        return RouteFunnelOut(
            route_id=route.id,
            started=started,
            completed=completed,
            stops=[
                FunnelStopOut(
                    stop_id=stop.id,
                    position=stop.position,
                    title=titles.get(stop.point_id, ""),
                    visits=visits.get(stop.id, 0),
                )
                for stop in sorted(route.stops, key=lambda item: item.position)
            ],
        )

    async def playback(self, days: int) -> list[PlaybackActivityOut]:
        return [
            PlaybackActivityOut(
                point_id=item.point_id,
                asset_id=item.asset_id,
                sessions=item.sessions,
                completed=item.completed,
                average_ratio=round(item.average_ratio, 3),
            )
            for item in await self._repository.playback(utcnow() - timedelta(days=days))
        ]

    async def _point_titles(self, point_ids: set[UUID]) -> dict[UUID, str]:
        if not point_ids:
            return {}
        points = await self._points.get_many(Point.id.in_(point_ids))
        return {point.id: resolve_text(point.title, self._language, self._fallback) or "" for point in points}
