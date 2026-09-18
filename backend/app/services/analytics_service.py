from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analytics_repo import ALLOWED_PERIODS, AnalyticsRepository


@dataclass(slots=True)
class DailyPointDTO:
    day: date
    plays: int
    visitors: int
    listened_seconds: float


@dataclass(slots=True)
class BreakdownItemDTO:
    name: str
    plays: int
    visitors: int


@dataclass(slots=True)
class TopTrackDTO:
    id: int
    title: str
    slug: str
    plays: int


@dataclass(slots=True)
class OverviewKpiDTO:
    plays: int
    visitors: int
    total_listened_seconds: float
    avg_completion: float | None
    completion_rate: float | None
    plays_today: int


@dataclass(slots=True)
class OverviewDTO:
    kpi: OverviewKpiDTO
    daily: list[DailyPointDTO]
    top_tracks: list[TopTrackDTO]
    devices: list[BreakdownItemDTO]
    referrers: list[BreakdownItemDTO]
    languages: list[BreakdownItemDTO]


@dataclass(slots=True)
class TrackRowDTO:
    id: int
    title: str
    slug: str
    is_published: bool
    plays: int
    visitors: int
    listened_seconds: float
    avg_completion: float | None
    median_completion: float | None
    completion_rate: float | None
    last_played_at: datetime | None


@dataclass(slots=True)
class HistogramBucketDTO:
    bucket_start: float
    count: int


@dataclass(slots=True)
class RecentSessionDTO:
    created_at: datetime
    listened_seconds: float
    completion_ratio: float | None
    is_completed: bool
    device_type: str | None
    referrer: str | None


@dataclass(slots=True)
class TrackDetailDTO:
    id: int
    title: str
    slug: str
    is_published: bool
    kpi: OverviewKpiDTO
    daily: list[DailyPointDTO]
    histogram: list[HistogramBucketDTO]
    avg_seek_count: float | None
    recent: list[RecentSessionDTO]


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = AnalyticsRepository(session)

    @staticmethod
    def validate_period(days: int) -> int:
        if days not in ALLOWED_PERIODS:
            raise ValueError(f"days must be one of {ALLOWED_PERIODS}")
        return days

    async def overview(self, days: int) -> OverviewDTO:
        data = await self.repo.overview(days)
        kpi = data["kpi"]
        return OverviewDTO(
            kpi=OverviewKpiDTO(
                plays=kpi.plays,
                visitors=kpi.visitors,
                total_listened_seconds=kpi.total_listened,
                avg_completion=kpi.avg_completion,
                completion_rate=kpi.completion_rate,
                plays_today=data["plays_today"],
            ),
            daily=[
                DailyPointDTO(
                    day=row.day.date(),
                    plays=row.plays,
                    visitors=row.visitors,
                    listened_seconds=row.listened_seconds,
                )
                for row in data["daily"]
            ],
            top_tracks=[
                TopTrackDTO(id=row.id, title=row.title, slug=row.slug, plays=row.plays)
                for row in data["top_tracks"]
            ],
            devices=self._breakdown(data["devices"]),
            referrers=self._breakdown(data["referrers"]),
            languages=self._breakdown(data["languages"]),
        )

    @staticmethod
    def _breakdown(rows) -> list[BreakdownItemDTO]:
        return [
            BreakdownItemDTO(name=row.name, plays=row.plays, visitors=row.visitors)
            for row in rows
        ]

    async def track_rows(self, days: int) -> list[TrackRowDTO]:
        rows = await self.repo.track_rows(days)
        return [
            TrackRowDTO(
                id=row.id,
                title=row.title,
                slug=row.slug,
                is_published=row.is_published,
                plays=row.plays or 0,
                visitors=row.visitors or 0,
                listened_seconds=row.listened_seconds or 0.0,
                avg_completion=row.avg_completion,
                median_completion=row.median_completion,
                completion_rate=row.completion_rate,
                last_played_at=row.last_played_at,
            )
            for row in rows
        ]

    async def track_detail(self, track_id: int, days: int) -> TrackDetailDTO | None:
        data = await self.repo.track_detail(track_id, days)
        if data is None:
            return None
        track = data["track"]
        kpi = data["kpi"]
        return TrackDetailDTO(
            id=track.id,
            title=track.title,
            slug=track.slug,
            is_published=track.is_published,
            kpi=OverviewKpiDTO(
                plays=kpi.plays,
                visitors=kpi.visitors,
                total_listened_seconds=kpi.total_listened,
                avg_completion=kpi.avg_completion,
                completion_rate=kpi.completion_rate,
                plays_today=0,
            ),
            daily=[
                DailyPointDTO(
                    day=row.day.date(),
                    plays=row.plays,
                    visitors=row.visitors,
                    listened_seconds=row.listened_seconds,
                )
                for row in data["daily"]
            ],
            histogram=[
                HistogramBucketDTO(
                    bucket_start=(row.bucket - 1) / 10.0,
                    count=row.count,
                )
                for row in data["histogram"]
            ],
            avg_seek_count=kpi.avg_seek_count,
            recent=[
                RecentSessionDTO(
                    created_at=s.created_at,
                    listened_seconds=s.listened_seconds,
                    completion_ratio=s.completion_ratio,
                    is_completed=s.is_completed,
                    device_type=s.device_type,
                    referrer=s.referrer,
                )
                for s in data["recent"]
            ],
        )
