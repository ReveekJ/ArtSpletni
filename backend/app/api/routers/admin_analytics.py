from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.admin import require_admin
from app.core.db import get_session
from app.services.analytics_service import (
    AnalyticsService,
    BreakdownItemDTO,
    OverviewDTO,
    TrackDetailDTO,
)

router = APIRouter(
    prefix="/api/admin/analytics",
    tags=["admin-analytics"],
    dependencies=[Depends(require_admin)],
)


class DailyPoint(BaseModel):
    day: date
    plays: int
    visitors: int
    listened_seconds: float


class BreakdownItem(BaseModel):
    name: str
    plays: int
    visitors: int


class TopTrack(BaseModel):
    id: int
    title: str
    slug: str
    plays: int


class OverviewKpi(BaseModel):
    plays: int
    visitors: int
    total_listened_seconds: float
    avg_completion: float | None
    completion_rate: float | None
    plays_today: int


class OverviewResponse(BaseModel):
    kpi: OverviewKpi
    daily: list[DailyPoint]
    top_tracks: list[TopTrack]
    devices: list[BreakdownItem]
    referrers: list[BreakdownItem]
    languages: list[BreakdownItem]


class TrackRow(BaseModel):
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


class TracksResponse(BaseModel):
    tracks: list[TrackRow]


class HistogramBucket(BaseModel):
    bucket_start: float
    count: int


class RecentSession(BaseModel):
    created_at: datetime
    listened_seconds: float
    completion_ratio: float | None
    is_completed: bool
    device_type: str | None
    referrer: str | None


class TrackDetailResponse(BaseModel):
    id: int
    title: str
    slug: str
    is_published: bool
    kpi: OverviewKpi
    daily: list[DailyPoint]
    histogram: list[HistogramBucket]
    avg_seek_count: float | None
    recent: list[RecentSession]


def get_analytics_service(
    session: AsyncSession = Depends(get_session),
) -> AnalyticsService:
    return AnalyticsService(session)


def _period(days: int) -> int:
    try:
        return AnalyticsService.validate_period(days)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "/overview",
    response_model=OverviewResponse,
    summary="Aggregated listening analytics overview for a period",
)
async def get_overview(
    days: int = Query(default=7),
    service: AnalyticsService = Depends(get_analytics_service),
) -> OverviewResponse:
    return _overview_to_response(await service.overview(_period(days)))


@router.get(
    "/tracks",
    response_model=TracksResponse,
    summary="Per-track listening stats for a period",
)
async def get_tracks(
    days: int = Query(default=7),
    service: AnalyticsService = Depends(get_analytics_service),
) -> TracksResponse:
    rows = await service.track_rows(_period(days))
    return TracksResponse(
        tracks=[
            TrackRow(
                id=r.id,
                title=r.title,
                slug=r.slug,
                is_published=r.is_published,
                plays=r.plays,
                visitors=r.visitors,
                listened_seconds=r.listened_seconds,
                avg_completion=r.avg_completion,
                median_completion=r.median_completion,
                completion_rate=r.completion_rate,
                last_played_at=r.last_played_at,
            )
            for r in rows
        ]
    )


@router.get(
    "/tracks/{track_id}",
    response_model=TrackDetailResponse,
    summary="Detailed listening analytics for a single track",
    responses={404: {"description": "Track not found"}},
)
async def get_track_detail(
    track_id: int,
    days: int = Query(default=7),
    service: AnalyticsService = Depends(get_analytics_service),
) -> TrackDetailResponse:
    detail = await service.track_detail(track_id, _period(days))
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )
    return _detail_to_response(detail)


def _overview_to_response(dto: OverviewDTO) -> OverviewResponse:
    return OverviewResponse(
        kpi=OverviewKpi(
            plays=dto.kpi.plays,
            visitors=dto.kpi.visitors,
            total_listened_seconds=dto.kpi.total_listened_seconds,
            avg_completion=dto.kpi.avg_completion,
            completion_rate=dto.kpi.completion_rate,
            plays_today=dto.kpi.plays_today,
        ),
        daily=[
            DailyPoint(
                day=p.day,
                plays=p.plays,
                visitors=p.visitors,
                listened_seconds=p.listened_seconds,
            )
            for p in dto.daily
        ],
        top_tracks=[
            TopTrack(id=t.id, title=t.title, slug=t.slug, plays=t.plays)
            for t in dto.top_tracks
        ],
        devices=_breakdown(dto.devices),
        referrers=_breakdown(dto.referrers),
        languages=_breakdown(dto.languages),
    )


def _breakdown(items: list[BreakdownItemDTO]) -> list[BreakdownItem]:
    return [
        BreakdownItem(name=i.name, plays=i.plays, visitors=i.visitors) for i in items
    ]


def _detail_to_response(dto: TrackDetailDTO) -> TrackDetailResponse:
    return TrackDetailResponse(
        id=dto.id,
        title=dto.title,
        slug=dto.slug,
        is_published=dto.is_published,
        kpi=OverviewKpi(
            plays=dto.kpi.plays,
            visitors=dto.kpi.visitors,
            total_listened_seconds=dto.kpi.total_listened_seconds,
            avg_completion=dto.kpi.avg_completion,
            completion_rate=dto.kpi.completion_rate,
            plays_today=dto.kpi.plays_today,
        ),
        daily=[
            DailyPoint(
                day=p.day,
                plays=p.plays,
                visitors=p.visitors,
                listened_seconds=p.listened_seconds,
            )
            for p in dto.daily
        ],
        histogram=[
            HistogramBucket(bucket_start=b.bucket_start, count=b.count)
            for b in dto.histogram
        ],
        avg_seek_count=dto.avg_seek_count,
        recent=[
            RecentSession(
                created_at=s.created_at,
                listened_seconds=s.listened_seconds,
                completion_ratio=s.completion_ratio,
                is_completed=s.is_completed,
                device_type=s.device_type,
                referrer=s.referrer,
            )
            for s in dto.recent
        ],
    )
