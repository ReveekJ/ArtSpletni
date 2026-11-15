from datetime import date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import Date, Select, cast, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OfferGrant, Point, PointKind, RouteRun, RunStatus, Unlock


class ProgressStats:
    def __init__(self, session: AsyncSession, timezone: str) -> None:
        self._session = session
        self._tz = ZoneInfo(timezone)

    def local_date(self, moment: datetime) -> date:
        return moment.astimezone(self._tz).date()

    def local_hour(self, moment: datetime) -> int:
        return moment.astimezone(self._tz).hour

    async def unlocked_count(self, user_id: UUID) -> int:
        return await self._scalar(select(func.count()).select_from(Unlock).where(Unlock.user_id == user_id))

    async def partner_points_count(self, user_id: UUID) -> int:
        return await self._scalar(
            select(func.count())
            .select_from(Unlock)
            .join(Point, Point.id == Unlock.point_id)
            .where(Unlock.user_id == user_id, Point.kind == PointKind.PARTNER)
        )

    async def completed_routes_count(self, user_id: UUID) -> int:
        return await self._scalar(
            select(func.count(distinct(RouteRun.route_id))).where(
                RouteRun.user_id == user_id, RouteRun.status == RunStatus.COMPLETED
            )
        )

    async def has_completed(self, user_id: UUID, route_id: UUID) -> bool:
        return (
            await self._scalar(
                select(func.count()).where(
                    RouteRun.user_id == user_id,
                    RouteRun.route_id == route_id,
                    RouteRun.status == RunStatus.COMPLETED,
                )
            )
            > 0
        )

    async def finishers_count(self, route_id: UUID) -> int:
        return await self._scalar(
            select(func.count(distinct(RouteRun.user_id))).where(
                RouteRun.route_id == route_id, RouteRun.status == RunStatus.COMPLETED
            )
        )

    async def redeemed_count(self, user_id: UUID) -> int:
        return await self._scalar(
            select(func.count()).where(OfferGrant.user_id == user_id, OfferGrant.redeemed_at.is_not(None))
        )

    async def unlocks_on(self, user_id: UUID, day: date) -> int:
        return sum(1 for unlock_day in await self._unlock_days(user_id) if unlock_day == day)

    async def streak_ending(self, user_id: UUID, day: date) -> int:
        days = set(await self._unlock_days(user_id))
        streak = 0
        while day - timedelta(days=streak) in days:
            streak += 1
        return streak

    async def _unlock_days(self, user_id: UUID) -> list[date]:
        local = func.timezone(str(self._tz), Unlock.created_at)
        rows = await self._session.execute(select(cast(local, Date)).where(Unlock.user_id == user_id))
        return list(rows.scalars())

    async def _scalar(self, statement: Select[int]) -> int:
        result = await self._session.execute(statement)
        return result.scalar_one()
