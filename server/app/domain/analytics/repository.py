from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    OfferGrant,
    PlaybackEvent,
    RouteRun,
    RunStatus,
    ScanEvent,
    ScanOutcome,
    StopVisit,
    User,
    UserKind,
)

FAILED_SCANS = (ScanOutcome.INVALID_TAG, ScanOutcome.POINT_UNAVAILABLE)


@dataclass(frozen=True, slots=True)
class Overview:
    scans: int
    failed_scans: int
    active_users: int
    new_accounts: int
    runs_started: int
    runs_completed: int
    offers_granted: int
    offers_redeemed: int


@dataclass(frozen=True, slots=True)
class PointActivity:
    point_id: UUID
    scans: int
    unique_users: int


@dataclass(frozen=True, slots=True)
class PlaybackActivity:
    point_id: UUID
    asset_id: UUID
    sessions: int
    completed: int
    average_ratio: float


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def overview(self, since: datetime) -> Overview:
        valid_scans = ScanEvent.outcome.not_in(FAILED_SCANS)
        return Overview(
            scans=await self._count(select(func.count()).where(ScanEvent.created_at >= since, valid_scans)),
            failed_scans=await self._count(
                select(func.count()).where(ScanEvent.created_at >= since, ScanEvent.outcome.in_(FAILED_SCANS))
            ),
            active_users=await self._count(
                select(func.count(distinct(ScanEvent.user_id))).where(ScanEvent.created_at >= since)
            ),
            new_accounts=await self._count(
                select(func.count()).where(User.created_at >= since, User.kind == UserKind.REGISTERED)
            ),
            runs_started=await self._count(select(func.count()).where(RouteRun.created_at >= since)),
            runs_completed=await self._count(
                select(func.count()).where(
                    RouteRun.completed_at >= since, RouteRun.status == RunStatus.COMPLETED
                )
            ),
            offers_granted=await self._count(select(func.count()).where(OfferGrant.created_at >= since)),
            offers_redeemed=await self._count(select(func.count()).where(OfferGrant.redeemed_at >= since)),
        )

    async def point_activity(self, since: datetime) -> list[PointActivity]:
        rows = await self._session.execute(
            select(ScanEvent.point_id, func.count(), func.count(distinct(ScanEvent.user_id)))
            .where(
                ScanEvent.created_at >= since,
                ScanEvent.point_id.is_not(None),
                ScanEvent.outcome.not_in(FAILED_SCANS),
            )
            .group_by(ScanEvent.point_id)
            .order_by(func.count().desc())
        )
        return [
            PointActivity(point_id=point_id, scans=scans, unique_users=users)
            for point_id, scans, users in rows.tuples()
            if point_id is not None
        ]

    async def route_funnel(self, route_id: UUID) -> tuple[int, int, dict[UUID, int]]:
        started = await self._count(select(func.count()).where(RouteRun.route_id == route_id))
        completed = await self._count(
            select(func.count()).where(RouteRun.route_id == route_id, RouteRun.status == RunStatus.COMPLETED)
        )
        rows = await self._session.execute(
            select(StopVisit.stop_id, func.count())
            .join(RouteRun, RouteRun.id == StopVisit.run_id)
            .where(RouteRun.route_id == route_id)
            .group_by(StopVisit.stop_id)
        )
        return started, completed, dict(rows.tuples().all())

    async def playback(self, since: datetime) -> list[PlaybackActivity]:
        ratio = func.least(PlaybackEvent.position_seconds / func.nullif(PlaybackEvent.duration_seconds, 0), 1)
        rows = await self._session.execute(
            select(
                PlaybackEvent.point_id,
                PlaybackEvent.asset_id,
                func.count(),
                func.count().filter(PlaybackEvent.completed.is_(True)),
                func.coalesce(func.avg(ratio), 0.0),
            )
            .where(PlaybackEvent.created_at >= since)
            .group_by(PlaybackEvent.point_id, PlaybackEvent.asset_id)
        )
        return [
            PlaybackActivity(point_id, asset_id, sessions, completed, float(average))
            for point_id, asset_id, sessions, completed, average in rows.tuples()
        ]

    async def _count(self, statement: Select[int]) -> int:
        return (await self._session.execute(statement)).scalar_one()
