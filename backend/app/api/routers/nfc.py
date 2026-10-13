from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_session
from app.entities.user import User
from app.repositories.audio_track_repo import AudioTrackRepository
from app.repositories.checkpoint_repo import CheckpointRepository
from app.repositories.route_stop_repo import RouteStopRepository
from app.services.progress_service import ProgressService
from app.services.track_access_service import TrackAccessService

router = APIRouter(prefix="/api/nfc", tags=["nfc"])
ACCESS_COOKIE_NAME = "spletni_track_access"


async def _get_user_from_session(
    request: Request,
    session: AsyncSession,
) -> User | None:
    from app.services.auth_service import AuthService

    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return await AuthService(session).get_by_id(user_id)


@router.get(
    "/{stop_type}/{slug}",
    include_in_schema=False,
)
async def nfc_bootstrap(
    stop_type: str,
    slug: str,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> Response:
    if stop_type not in ("track", "checkpoint"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown NFC target type",
        )

    stop_repo = RouteStopRepository(session)
    progress_service = ProgressService(session)

    if stop_type == "track":
        track_repo = AudioTrackRepository(session)
        track = await track_repo.get_by_slug(slug)
        if track is None or track.moderation_status != "published":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found",
            )
        route_stops = await stop_repo.find_route_stops_for_track(track.id)
        if route_stops:
            user = await _get_user_from_session(request, session)
            if user is None:
                response.status_code = status.HTTP_302_FOUND
                response.headers["Location"] = (
                    f"/login?next=/api/nfc/track/{slug}"
                )
                return response
            for stop in route_stops:
                if not await progress_service.is_stop_unlocked(stop, user):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Previous stops must be completed first",
                    )
                if stop.completion_criteria in ("scan", "open"):
                    await progress_service.record_completion(user, stop)
            response.status_code = status.HTTP_302_FOUND
            response.headers["Location"] = f"/t/{track.slug}"
            return response

        access_service = TrackAccessService(
            session, get_settings().track_access_ttl_seconds,
        )
        secret = await access_service.create_grant(track)
        response.set_cookie(
            ACCESS_COOKIE_NAME,
            secret,
            max_age=get_settings().track_access_ttl_seconds,
            httponly=True,
            secure=get_settings().track_access_cookie_secure,
            samesite="lax",
            path="/",
        )
        response.status_code = status.HTTP_302_FOUND
        response.headers["Location"] = f"/t/{track.slug}"
        return response

    cp_repo = CheckpointRepository(session)
    cp = await cp_repo.get_by_slug(slug)
    if cp is None or not cp.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checkpoint not found",
        )
    route_stops = await stop_repo.find_route_stops_for_checkpoint(cp.id)
    if route_stops:
        user = await _get_user_from_session(request, session)
        if user is None:
            response.status_code = status.HTTP_302_FOUND
            response.headers["Location"] = (
                f"/login?next=/api/nfc/checkpoint/{slug}"
            )
            return response
        for stop in route_stops:
            if not await progress_service.is_stop_unlocked(stop, user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Previous stops must be completed first",
                )
            if stop.completion_criteria in ("scan", "open"):
                await progress_service.record_completion(user, stop)
    response.status_code = status.HTTP_302_FOUND
    response.headers["Location"] = f"/c/{cp.slug}"
    return response
