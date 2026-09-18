from datetime import UTC, datetime, timedelta

from sqlalchemy import String, and_, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.entities.audio_track import AudioTrack
from app.entities.listen_session import ListenSession

ALLOWED_PERIODS = (7, 30, 90)


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _since(self, days: int) -> datetime:
        return datetime.now(UTC) - timedelta(days=days)

    def _period_filter(self, days: int) -> ColumnElement[bool]:
        return ListenSession.created_at >= self._since(days)

    async def overview(self, days: int) -> dict:
        period = self._period_filter(days)
        day_expr = func.date_trunc("day", ListenSession.created_at)

        kpi_stmt = select(
            func.count(ListenSession.id).label("plays"),
            func.count(func.distinct(ListenSession.visitor_id)).label("visitors"),
            func.coalesce(func.sum(ListenSession.listened_seconds), 0.0).label(
                "total_listened"
            ),
            func.avg(ListenSession.completion_ratio).label("avg_completion"),
            func.avg(
                case((ListenSession.is_completed.is_(True), 1.0), else_=0.0)
            ).label("completion_rate"),
        ).where(period)

        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        today_stmt = select(func.count(ListenSession.id)).where(
            ListenSession.created_at >= today_start
        )

        daily_stmt = (
            select(
                day_expr.label("day"),
                func.count(ListenSession.id).label("plays"),
                func.count(func.distinct(ListenSession.visitor_id)).label("visitors"),
                func.coalesce(func.sum(ListenSession.listened_seconds), 0.0).label(
                    "listened_seconds"
                ),
            )
            .where(period)
            .group_by(day_expr)
            .order_by(day_expr)
        )

        top_stmt = (
            select(
                AudioTrack.id,
                AudioTrack.title,
                AudioTrack.slug,
                func.count(ListenSession.id).label("plays"),
            )
            .join(ListenSession, ListenSession.track_id == AudioTrack.id)
            .where(period)
            .group_by(AudioTrack.id)
            .order_by(func.count(ListenSession.id).desc())
            .limit(5)
        )

        device_stmt = self._breakdown(ListenSession.device_type, days)
        referrer_stmt = self._breakdown(ListenSession.referrer, days)
        language_stmt = self._breakdown(ListenSession.language, days)

        kpi = (await self.session.execute(kpi_stmt)).one()
        plays_today = (await self.session.execute(today_stmt)).scalar_one()
        daily = (await self.session.execute(daily_stmt)).all()
        top = (await self.session.execute(top_stmt)).all()
        devices = (await self.session.execute(device_stmt)).all()
        referrers = (await self.session.execute(referrer_stmt)).all()
        languages = (await self.session.execute(language_stmt)).all()

        return {
            "kpi": kpi,
            "plays_today": plays_today,
            "daily": daily,
            "top_tracks": top,
            "devices": devices,
            "referrers": referrers,
            "languages": languages,
        }

    def _breakdown(self, column, days: int):
        return (
            select(
                func.coalesce(cast(column, String), "unknown").label("name"),
                func.count(ListenSession.id).label("plays"),
                func.count(func.distinct(ListenSession.visitor_id)).label("visitors"),
            )
            .where(self._period_filter(days))
            .group_by("name")
            .order_by(func.count(ListenSession.id).desc())
            .limit(10)
        )

    async def track_rows(self, days: int) -> list:
        period = self._period_filter(days)
        plays = (
            select(
                ListenSession.track_id.label("track_id"),
                func.count(ListenSession.id).label("plays"),
                func.count(func.distinct(ListenSession.visitor_id)).label("visitors"),
                func.coalesce(func.sum(ListenSession.listened_seconds), 0.0).label(
                    "listened_seconds"
                ),
                func.avg(ListenSession.completion_ratio).label("avg_completion"),
                func.percentile_cont(0.5).within_group(
                    ListenSession.completion_ratio
                ).label("median_completion"),
                func.avg(
                    case((ListenSession.is_completed.is_(True), 1.0), else_=0.0)
                ).label("completion_rate"),
                func.max(ListenSession.created_at).label("last_played_at"),
            )
            .where(period)
            .group_by(ListenSession.track_id)
            .subquery()
        )

        stmt = (
            select(
                AudioTrack.id,
                AudioTrack.title,
                AudioTrack.slug,
                AudioTrack.is_published,
                plays.c.plays,
                plays.c.visitors,
                plays.c.listened_seconds,
                plays.c.avg_completion,
                plays.c.median_completion,
                plays.c.completion_rate,
                plays.c.last_played_at,
            )
            .outerjoin(plays, plays.c.track_id == AudioTrack.id)
            .order_by(func.coalesce(plays.c.plays, 0).desc(), AudioTrack.id)
        )
        result = await self.session.execute(stmt)
        return result.all()

    async def track_detail(self, track_id: int, days: int) -> dict | None:
        track = await self.session.get(AudioTrack, track_id)
        if track is None:
            return None

        period = self._period_filter(days)
        day_expr = func.date_trunc("day", ListenSession.created_at)

        daily_stmt = (
            select(
                day_expr.label("day"),
                func.count(ListenSession.id).label("plays"),
                func.count(func.distinct(ListenSession.visitor_id)).label("visitors"),
                func.coalesce(func.sum(ListenSession.listened_seconds), 0.0).label(
                    "listened_seconds"
                ),
            )
            .where(and_(period, ListenSession.track_id == track_id))
            .group_by(day_expr)
            .order_by(day_expr)
        )

        bucket_expr = func.width_bucket(
            ListenSession.completion_ratio, 0.0, 1.0, 10
        ).label("bucket")
        histogram_stmt = (
            select(bucket_expr, func.count(ListenSession.id).label("count"))
            .where(and_(period, ListenSession.track_id == track_id))
            .group_by(bucket_expr)
            .order_by(bucket_expr)
        )

        kpi_stmt = select(
            func.count(ListenSession.id).label("plays"),
            func.count(func.distinct(ListenSession.visitor_id)).label("visitors"),
            func.coalesce(func.sum(ListenSession.listened_seconds), 0.0).label(
                "total_listened"
            ),
            func.avg(ListenSession.completion_ratio).label("avg_completion"),
            func.avg(
                case((ListenSession.is_completed.is_(True), 1.0), else_=0.0)
            ).label("completion_rate"),
            func.avg(ListenSession.seek_count).label("avg_seek_count"),
        ).where(and_(period, ListenSession.track_id == track_id))

        recent_stmt = (
            select(ListenSession)
            .where(and_(period, ListenSession.track_id == track_id))
            .order_by(ListenSession.created_at.desc())
            .limit(20)
        )

        daily = (await self.session.execute(daily_stmt)).all()
        histogram = (await self.session.execute(histogram_stmt)).all()
        kpi = (await self.session.execute(kpi_stmt)).one()
        recent = (await self.session.execute(recent_stmt)).scalars().all()

        return {
            "track": track,
            "kpi": kpi,
            "daily": daily,
            "histogram": histogram,
            "recent": recent,
        }

    async def track_by_id(self, track_id: int) -> AudioTrack | None:
        return await self.session.get(AudioTrack, track_id)
