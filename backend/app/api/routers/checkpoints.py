from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import get_current_user
from app.core.db import get_session
from app.entities.user import User
from app.repositories.checkpoint_repo import CheckpointRepository
from app.repositories.route_stop_repo import RouteStopRepository
from app.services.checkpoint_service import CheckpointService
from app.services.progress_service import ProgressService
from app.services.storage_service import get_storage

router = APIRouter(prefix="/api/checkpoints", tags=["checkpoints"])


class CheckpointResponse(BaseModel):
    id: int
    slug: str
    title: str
    description: str | None
    latitude: float
    longitude: float
    location_name: str | None
    content_type: str
    text_content: str | None
    image_url: str | None
    loot_type: str | None
    loot_value: str | None
    audio_url: str | None


@router.get(
    "/{slug}",
    response_model=CheckpointResponse,
    responses={404: {"description": "Checkpoint not found"}},
    summary="Get a published checkpoint by slug",
)
async def get_checkpoint(
    slug: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: User | None = Depends(get_current_user),
) -> CheckpointResponse:
    service = CheckpointService(session, get_storage())
    dto = await service.get_published_by_slug(slug)
    if dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checkpoint not found",
        )

    stop_repo = RouteStopRepository(session)
    cp_repo = CheckpointRepository(session)
    cp = await cp_repo.get_by_slug(slug)
    if cp is not None:
        route_stops = await stop_repo.find_route_stops_for_checkpoint(cp.id)
        if route_stops and user is not None:
            progress_service = ProgressService(session)
            for stop in route_stops:
                if not await progress_service.is_stop_unlocked(stop, user):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Previous stops must be completed first",
                    )

    return CheckpointResponse(
        id=dto.id,
        slug=dto.slug,
        title=dto.title,
        description=dto.description,
        latitude=dto.latitude,
        longitude=dto.longitude,
        location_name=dto.location_name,
        content_type=dto.content_type,
        text_content=dto.text_content,
        image_url=dto.image_url,
        loot_type=dto.loot_type,
        loot_value=dto.loot_value,
        audio_url=dto.audio_url,
    )
