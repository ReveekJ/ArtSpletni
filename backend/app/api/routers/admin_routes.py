from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.admin import require_admin
from app.core.db import get_session
from app.services.checkpoint_service import CheckpointService
from app.services.route_service import RouteService
from app.services.storage_service import get_storage

router = APIRouter(
    prefix="/api/admin/routes",
    tags=["admin-routes"],
    dependencies=[Depends(require_admin)],
)


class RouteCreatePayload(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


class RouteUpdatePayload(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_published: bool | None = None


class RouteAdminItem(BaseModel):
    id: int
    slug: str
    title: str
    description: str | None
    is_published: bool


class RouteAdminList(BaseModel):
    routes: list[RouteAdminItem]


class StopCreatePayload(BaseModel):
    stop_type: Literal["track", "checkpoint"]
    track_id: int | None = None
    checkpoint_id: int | None = None
    completion_criteria: Literal[
        "scan", "listen_any", "listen_95", "listen_100", "open"
    ] = "scan"


class StopUpdatePayload(BaseModel):
    completion_criteria: (
        Literal["scan", "listen_any", "listen_95", "listen_100", "open"] | None
    ) = None
    order_index: int | None = None


class StopAdminResponse(BaseModel):
    id: int
    route_id: int
    order_index: int
    stop_type: str
    track_id: int | None
    checkpoint_id: int | None
    completion_criteria: str
    depends_on: list[int] = []


class DependencyPayload(BaseModel):
    depends_on_stop_id: int


class ReorderPayload(BaseModel):
    stop_ids: list[int]


def get_route_service(
    session: AsyncSession = Depends(get_session),
) -> RouteService:
    return RouteService(session, get_storage())


def get_checkpoint_service(
    session: AsyncSession = Depends(get_session),
) -> CheckpointService:
    return CheckpointService(session, get_storage())


@router.get("", response_model=RouteAdminList, summary="List all routes (admin)")
async def list_routes(
    service: RouteService = Depends(get_route_service),
) -> RouteAdminList:
    routes = await service.list_all()
    return RouteAdminList(
        routes=[
            RouteAdminItem(
                id=r.id,
                slug=r.slug,
                title=r.title,
                description=r.description,
                is_published=False,
            )
            for r in routes
        ],
    )


@router.post(
    "",
    response_model=RouteAdminItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new route (admin)",
)
async def create_route(
    payload: RouteCreatePayload,
    service: RouteService = Depends(get_route_service),
) -> RouteAdminItem:
    route = await service.create(payload.title, payload.description, None)
    return RouteAdminItem(
        id=route.id,
        slug=route.slug,
        title=route.title,
        description=route.description,
        is_published=route.is_published,
    )


@router.patch(
    "/{route_id}",
    response_model=RouteAdminItem,
    summary="Update a route (admin)",
    responses={404: {"description": "Route not found"}},
)
async def update_route(
    route_id: int,
    payload: RouteUpdatePayload,
    service: RouteService = Depends(get_route_service),
) -> RouteAdminItem:
    route = await service.repo.get_by_id(route_id)
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found",
        )
    route = await service.update(
        route,
        title=payload.title,
        description=payload.description,
        is_published=payload.is_published,
        cover_s3_key=None,
    )
    return RouteAdminItem(
        id=route.id,
        slug=route.slug,
        title=route.title,
        description=route.description,
        is_published=route.is_published,
    )


@router.delete(
    "/{route_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a route (admin)",
    responses={404: {"description": "Route not found"}},
)
async def delete_route(
    route_id: int,
    service: RouteService = Depends(get_route_service),
) -> None:
    route = await service.repo.get_by_id(route_id)
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found",
        )
    await service.delete(route)


@router.get(
    "/{route_id}/stops",
    response_model=list[StopAdminResponse],
    summary="List stops for a route (admin)",
)
async def list_stops(
    route_id: int,
    service: RouteService = Depends(get_route_service),
) -> list[StopAdminResponse]:
    stops = await service.stop_repo.list_by_route(route_id)
    all_deps = await service.stop_repo.get_all_dependencies_for_route(route_id)
    deps_map: dict[int, list[int]] = {}
    for dep in all_deps:
        deps_map.setdefault(dep.route_stop_id, []).append(dep.depends_on_stop_id)
    return [
        StopAdminResponse(
            id=s.id,
            route_id=s.route_id,
            order_index=s.order_index,
            stop_type=s.stop_type,
            track_id=s.track_id,
            checkpoint_id=s.checkpoint_id,
            completion_criteria=s.completion_criteria,
            depends_on=deps_map.get(s.id, []),
        )
        for s in stops
    ]


@router.post(
    "/{route_id}/stops",
    response_model=StopAdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a stop to a route (admin)",
    responses={404: {"description": "Route not found"}, 400: {"description": "Invalid stop"}},
)
async def add_stop(
    route_id: int,
    payload: StopCreatePayload,
    service: RouteService = Depends(get_route_service),
) -> StopAdminResponse:
    route = await service.repo.get_by_id(route_id)
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found",
        )
    if payload.stop_type == "track" and payload.track_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="track_id is required for track stops",
        )
    if payload.stop_type == "checkpoint" and payload.checkpoint_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="checkpoint_id is required for checkpoint stops",
        )
    stop = await service.add_stop(
        route_id=route_id,
        stop_type=payload.stop_type,
        track_id=payload.track_id,
        checkpoint_id=payload.checkpoint_id,
        completion_criteria=payload.completion_criteria,
    )
    return StopAdminResponse(
        id=stop.id,
        route_id=stop.route_id,
        order_index=stop.order_index,
        stop_type=stop.stop_type,
        track_id=stop.track_id,
        checkpoint_id=stop.checkpoint_id,
        completion_criteria=stop.completion_criteria,
        depends_on=[],
    )


@router.patch(
    "/{route_id}/stops/{stop_id}",
    response_model=StopAdminResponse,
    summary="Update a stop (admin)",
    responses={404: {"description": "Stop not found"}},
)
async def update_stop(
    route_id: int,
    stop_id: int,
    payload: StopUpdatePayload,
    service: RouteService = Depends(get_route_service),
) -> StopAdminResponse:
    stop = await service.stop_repo.get_by_id(stop_id)
    if stop is None or stop.route_id != route_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stop not found",
        )
    stop = await service.update_stop(
        stop,
        completion_criteria=payload.completion_criteria,
        order_index=payload.order_index,
    )
    deps = await service.stop_repo.get_dependencies(stop.id)
    return StopAdminResponse(
        id=stop.id,
        route_id=stop.route_id,
        order_index=stop.order_index,
        stop_type=stop.stop_type,
        track_id=stop.track_id,
        checkpoint_id=stop.checkpoint_id,
        completion_criteria=stop.completion_criteria,
        depends_on=[d.depends_on_stop_id for d in deps],
    )


@router.delete(
    "/{route_id}/stops/{stop_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a stop (admin)",
    responses={404: {"description": "Stop not found"}},
)
async def delete_stop(
    route_id: int,
    stop_id: int,
    service: RouteService = Depends(get_route_service),
) -> None:
    stop = await service.stop_repo.get_by_id(stop_id)
    if stop is None or stop.route_id != route_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stop not found",
        )
    await service.delete_stop(stop)


@router.post(
    "/{route_id}/stops/{stop_id}/dependencies",
    status_code=status.HTTP_201_CREATED,
    summary="Add a dependency to a stop (admin)",
    responses={
        404: {"description": "Stop not found"},
        400: {"description": "Invalid dependency or cycle detected"},
    },
)
async def add_dependency(
    route_id: int,
    stop_id: int,
    payload: DependencyPayload,
    service: RouteService = Depends(get_route_service),
) -> dict[str, str]:
    stop = await service.stop_repo.get_by_id(stop_id)
    if stop is None or stop.route_id != route_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stop not found",
        )
    dep_stop = await service.stop_repo.get_by_id(payload.depends_on_stop_id)
    if dep_stop is None or dep_stop.route_id != route_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dependency stop not found in this route",
        )
    try:
        await service.add_dependency(stop_id, payload.depends_on_stop_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return {"status": "ok"}


@router.delete(
    "/{route_id}/stops/{stop_id}/dependencies/{depends_on_stop_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a dependency from a stop (admin)",
)
async def remove_dependency(
    route_id: int,
    stop_id: int,
    depends_on_stop_id: int,
    service: RouteService = Depends(get_route_service),
) -> None:
    await service.remove_dependency(stop_id, depends_on_stop_id)


@router.post(
    "/{route_id}/reorder",
    summary="Reorder stops in a route (admin)",
)
async def reorder_stops(
    route_id: int,
    payload: ReorderPayload,
    service: RouteService = Depends(get_route_service),
) -> dict[str, str]:
    await service.reorder_stops(route_id, payload.stop_ids)
    return {"status": "ok"}


# --- Checkpoint CRUD (admin) ---


class CheckpointCreatePayload(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content_type: Literal["text", "image", "loot", "audio"]
    description: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    location_name: str | None = Field(default=None, max_length=255)
    text_content: str | None = None
    loot_type: Literal["promo_code", "link", "badge"] | None = None
    loot_value: str | None = None
    is_published: bool = False


class CheckpointUpdatePayload(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content_type: Literal["text", "image", "loot", "audio"] | None = None
    description: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    location_name: str | None = Field(default=None, max_length=255)
    text_content: str | None = None
    loot_type: Literal["promo_code", "link", "badge"] | None = None
    loot_value: str | None = None
    is_published: bool | None = None


class CheckpointAdminResponse(BaseModel):
    id: int
    slug: str
    title: str
    content_type: str
    description: str | None
    latitude: float
    longitude: float
    location_name: str | None
    text_content: str | None
    loot_type: str | None
    loot_value: str | None
    is_published: bool


class CheckpointAdminList(BaseModel):
    checkpoints: list[CheckpointAdminResponse]


checkpoint_router = APIRouter(
    prefix="/api/admin/checkpoints",
    tags=["admin-checkpoints"],
    dependencies=[Depends(require_admin)],
)


@checkpoint_router.get(
    "",
    response_model=CheckpointAdminList,
    summary="List all checkpoints (admin)",
)
async def list_checkpoints(
    service: CheckpointService = Depends(get_checkpoint_service),
) -> CheckpointAdminList:
    checkpoints = await service.list_all()
    return CheckpointAdminList(
        checkpoints=[
            CheckpointAdminResponse(
                id=cp.id,
                slug=cp.slug,
                title=cp.title,
                content_type=cp.content_type,
                description=cp.description,
                latitude=cp.latitude,
                longitude=cp.longitude,
                location_name=cp.location_name,
                text_content=cp.text_content,
                loot_type=cp.loot_type,
                loot_value=cp.loot_value,
                is_published=False,
            )
            for cp in checkpoints
        ],
    )


@checkpoint_router.post(
    "",
    response_model=CheckpointAdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a checkpoint (admin)",
)
async def create_checkpoint(
    payload: CheckpointCreatePayload,
    service: CheckpointService = Depends(get_checkpoint_service),
) -> CheckpointAdminResponse:
    cp = await service.create(
        title=payload.title,
        content_type=payload.content_type,
        description=payload.description,
        latitude=payload.latitude,
        longitude=payload.longitude,
        location_name=payload.location_name,
        text_content=payload.text_content,
        image_s3_key=None,
        loot_type=payload.loot_type,
        loot_value=payload.loot_value,
        audio_s3_key=None,
        is_published=payload.is_published,
    )
    return CheckpointAdminResponse(
        id=cp.id,
        slug=cp.slug,
        title=cp.title,
        content_type=cp.content_type,
        description=cp.description,
        latitude=cp.latitude,
        longitude=cp.longitude,
        location_name=cp.location_name,
        text_content=cp.text_content,
        loot_type=cp.loot_type,
        loot_value=cp.loot_value,
        is_published=cp.is_published,
    )


@checkpoint_router.patch(
    "/{checkpoint_id}",
    response_model=CheckpointAdminResponse,
    summary="Update a checkpoint (admin)",
    responses={404: {"description": "Checkpoint not found"}},
)
async def update_checkpoint(
    checkpoint_id: int,
    payload: CheckpointUpdatePayload,
    service: CheckpointService = Depends(get_checkpoint_service),
) -> CheckpointAdminResponse:
    cp = await service.repo.get_by_id(checkpoint_id)
    if cp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checkpoint not found",
        )
    cp = await service.update(
        cp,
        title=payload.title,
        content_type=payload.content_type,
        description=payload.description,
        latitude=payload.latitude,
        longitude=payload.longitude,
        location_name=payload.location_name,
        text_content=payload.text_content,
        loot_type=payload.loot_type,
        loot_value=payload.loot_value,
        is_published=payload.is_published,
    )
    return CheckpointAdminResponse(
        id=cp.id,
        slug=cp.slug,
        title=cp.title,
        content_type=cp.content_type,
        description=cp.description,
        latitude=cp.latitude,
        longitude=cp.longitude,
        location_name=cp.location_name,
        text_content=cp.text_content,
        loot_type=cp.loot_type,
        loot_value=cp.loot_value,
        is_published=cp.is_published,
    )


@checkpoint_router.delete(
    "/{checkpoint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a checkpoint (admin)",
    responses={404: {"description": "Checkpoint not found"}},
)
async def delete_checkpoint(
    checkpoint_id: int,
    service: CheckpointService = Depends(get_checkpoint_service),
) -> None:
    cp = await service.repo.get_by_id(checkpoint_id)
    if cp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checkpoint not found",
        )
    await service.delete(cp)
