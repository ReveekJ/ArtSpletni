from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_session
from app.entities.user import User
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=1, max_length=255)


class LoginPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    is_admin: bool


class SessionStatusResponse(BaseModel):
    authenticated: bool


def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    return AuthService(session)


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return await AuthService(session).get_by_id(user_id)


async def require_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User:
    user = await get_current_user(request, session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    responses={409: {"description": "Email already registered"}},
)
async def register(
    payload: RegisterPayload,
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    try:
        user = await service.register(payload.email, payload.password, payload.display_name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from exc
    request.session.update({"user_id": user.id})
    return _to_response(user)


@router.post(
    "/login",
    response_model=UserResponse,
    summary="Log in with email and password",
    responses={401: {"description": "Invalid credentials"}},
)
async def login(
    payload: LoginPayload,
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    user = await service.authenticate(payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    request.session.update({"user_id": user.id})
    return _to_response(user)


@router.delete(
    "/session",
    response_model=SessionStatusResponse,
    summary="Log out the current user",
)
async def logout(request: Request) -> SessionStatusResponse:
    request.session.clear()
    return SessionStatusResponse(authenticated=False)


@router.get(
    "/me",
    response_model=UserResponse | None,
    summary="Get current authenticated user info",
)
async def me(
    user: User | None = Depends(get_current_user),
) -> UserResponse | None:
    if user is None:
        return None
    return _to_response(user)


@router.get(
    "/yandex",
    summary="Redirect to Yandex OAuth authorization page",
    include_in_schema=False,
)
async def yandex_login(request: Request) -> dict[str, str]:
    settings = get_settings()
    if not settings.yandex_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Yandex OAuth not configured",
        )
    auth_url = (
        f"https://oauth.yandex.ru/authorize"
        f"?response_type=code"
        f"&client_id={settings.yandex_client_id}"
        f"&redirect_uri={settings.yandex_redirect_uri}"
    )
    return {"auth_url": auth_url}


@router.get(
    "/yandex/callback",
    summary="Handle Yandex OAuth callback",
    include_in_schema=False,
)
async def yandex_callback(
    code: str,
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    import httpx

    settings = get_settings()
    if not settings.yandex_client_id or not settings.yandex_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Yandex OAuth not configured",
        )

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth.yandex.ru/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.yandex_client_id,
                "client_secret": settings.yandex_client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Yandex OAuth token exchange failed",
            )
        access_token = token_resp.json()["access_token"]

        user_resp = await client.get(
            "https://login.yandex.ru/info",
            headers={"Authorization": f"OAuth {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to fetch Yandex user info",
            )
        yandex_user = user_resp.json()

    yandex_id = str(yandex_user["id"])
    email = yandex_user.get("default_email") or yandex_user.get("emails", [None])[0]
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yandex account has no email",
        )
    display_name = yandex_user.get("real_name") or yandex_user.get("login") or email

    user = await service.get_or_create_yandex_user(yandex_id, email, display_name)
    request.session.update({"user_id": user.id})
    return {"status": "ok", "email": user.email}


def _to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_admin=user.is_admin,
    )
