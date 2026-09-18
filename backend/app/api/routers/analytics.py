from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.services.listen_tracking_service import ListenSessionInput, ListenTrackingService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class ListenSessionPayload(BaseModel):
    slug: str = Field(min_length=1, max_length=32)
    session_token: str = Field(min_length=8, max_length=36)
    visitor_id: str = Field(min_length=8, max_length=36)
    track_duration_seconds: float | None = Field(default=None, ge=0)
    listened_seconds: float = Field(ge=0)
    last_position_seconds: float = Field(ge=0)
    seek_count: int = Field(ge=0)
    is_completed: bool = False
    referrer: str | None = Field(default=None, max_length=512)
    language: str | None = Field(default=None, max_length=16)


def get_listen_tracking_service(
    session: AsyncSession = Depends(get_session),
) -> ListenTrackingService:
    return ListenTrackingService(session)


@router.post(
    "/listen-sessions",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Record or update a listen session for a published track",
    responses={
        204: {"description": "Session recorded"},
        404: {"description": "Track not found or not published"},
    },
)
async def record_listen_session(
    payload: ListenSessionPayload,
    request: Request,
    service: ListenTrackingService = Depends(get_listen_tracking_service),
) -> Response:
    device_type = ListenTrackingService.parse_device_type(request.headers.get("user-agent"))
    recorded = await service.record(
        ListenSessionInput(
            slug=payload.slug,
            session_token=payload.session_token,
            visitor_id=payload.visitor_id,
            track_duration_seconds=payload.track_duration_seconds,
            listened_seconds=payload.listened_seconds,
            last_position_seconds=payload.last_position_seconds,
            seek_count=payload.seek_count,
            is_completed=payload.is_completed,
            referrer=payload.referrer,
            language=payload.language,
        ),
        device_type=device_type,
    )
    if not recorded:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
