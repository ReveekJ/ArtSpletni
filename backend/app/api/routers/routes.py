from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import get_current_user
from app.core.db import get_session
from app.entities.user import User
from app.services.progress_service import ProgressService
from app.services.route_service import RouteService
from app.services.storage_service import get_storage

router = APIRouter(prefix="/api/routes", tags=["routes"])


class StopResponse(BaseModel):
    id: int
    order_index: int
    stop_type: str
    track_id: int | None
    checkpoint_id: int | None
    completion_criteria: str
    title: str
    slug: str
    latitude: float
    longitude: float
    location_name: str | None
    depends_on: list[int]


class RouteResponse(BaseModel):
    id: int
    slug: str
    title: str
    description: str | None
    cover_url: str | None
    is_published: bool
    stops: list[StopResponse]


class RouteListItem(BaseModel):
    id: int
    slug: str
    title: str
    description: str | None
    cover_url: str | None


class RouteListResponse(BaseModel):
    routes: list[RouteListItem]


class StopStatusResponse(BaseModel):
    stop_id: int
    is_unlocked: bool
    is_completed: bool


class RouteProgressResponse(BaseModel):
    route_id: int
    total_stops: int
    completed_stops: int
    stop_statuses: list[StopStatusResponse]


def get_route_service(
    session: AsyncSession = Depends(get_session),
) -> RouteService:
    return RouteService(session, get_storage())


@router.get(
    "",
    response_model=RouteListResponse,
    summary="List published routes",
)
async def list_routes(
    service: RouteService = Depends(get_route_service),
) -> RouteListResponse:
    routes = await service.list_published()
    return RouteListResponse(
        routes=[
            RouteListItem(
                id=r.id,
                slug=r.slug,
                title=r.title,
                description=r.description,
                cover_url=r.cover_url,
            )
            for r in routes
        ],
    )


@router.get(
    "/{slug}",
    response_model=RouteResponse,
    responses={404: {"description": "Route not found"}},
    summary="Get a published route with all stops",
)
async def get_route(
    slug: str,
    service: RouteService = Depends(get_route_service),
) -> RouteResponse:
    dto = await service.get_published_by_slug(slug)
    if dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found",
        )
    return RouteResponse(
        id=dto.id,
        slug=dto.slug,
        title=dto.title,
        description=dto.description,
        cover_url=dto.cover_url,
        is_published=dto.is_published,
        stops=[
            StopResponse(
                id=s.id,
                order_index=s.order_index,
                stop_type=s.stop_type,
                track_id=s.track_id,
                checkpoint_id=s.checkpoint_id,
                completion_criteria=s.completion_criteria,
                title=s.title,
                slug=s.slug,
                latitude=s.latitude,
                longitude=s.longitude,
                location_name=s.location_name,
                depends_on=s.depends_on,
            )
            for s in dto.stops
        ],
    )


@router.get(
    "/{slug}/progress",
    response_model=RouteProgressResponse,
    summary="Get current user progress for a route",
)
async def get_route_progress(
    slug: str,
    service: RouteService = Depends(get_route_service),
    user: User | None = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RouteProgressResponse:
    dto = await service.get_published_by_slug(slug)
    if dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found",
        )
    progress_service = ProgressService(session)
    progress = await progress_service.get_route_progress(dto.id, user)
    return RouteProgressResponse(
        route_id=progress.route_id,
        total_stops=progress.total_stops,
        completed_stops=progress.completed_stops,
        stop_statuses=[
            StopStatusResponse(
                stop_id=s.stop_id,
                is_unlocked=s.is_unlocked,
                is_completed=s.is_completed,
            )
            for s in progress.stop_statuses
        ],
    )
