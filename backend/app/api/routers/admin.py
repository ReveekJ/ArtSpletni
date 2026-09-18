from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from starlette.status import HTTP_401_UNAUTHORIZED

from app.core.config import get_settings

router = APIRouter(prefix="/api/admin", tags=["admin"])


class LoginPayload(BaseModel):
    username: str
    password: str


class SessionStatusResponse(BaseModel):
    authenticated: bool


async def require_admin(request: Request) -> None:
    if not request.session.get("admin"):
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Not authenticated")


@router.post(
    "/session",
    response_model=SessionStatusResponse,
    summary="Log in to the admin dashboard (shared session with sqladmin)",
)
async def login(payload: LoginPayload, request: Request) -> SessionStatusResponse:
    settings = get_settings()
    if (
        payload.username != settings.admin_username
        or payload.password != settings.admin_password
    ):
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    request.session.update({"admin": True})
    return SessionStatusResponse(authenticated=True)


@router.delete(
    "/session",
    response_model=SessionStatusResponse,
    summary="Log out from the admin dashboard",
)
async def logout(request: Request) -> SessionStatusResponse:
    request.session.clear()
    return SessionStatusResponse(authenticated=False)


@router.get(
    "/session",
    response_model=SessionStatusResponse,
    summary="Check current admin session status",
)
async def session_status(request: Request) -> SessionStatusResponse:
    return SessionStatusResponse(authenticated=bool(request.session.get("admin")))
