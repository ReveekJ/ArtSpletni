import logging
from typing import Annotated

from litestar import Controller, Response, get, post
from litestar.di import NamedDependency, Provide
from litestar.params import FromQuery, JSONBody, QueryParameter
from litestar.response import Redirect
from litestar.status_codes import HTTP_200_OK, HTTP_202_ACCEPTED, HTTP_204_NO_CONTENT

from app.config import strict_rate_limit
from app.domain.auth.deps import (
    provide_account_merge_service,
    provide_auth_service,
    provide_guest_mergers,
    provide_password_reset_service,
    provide_users_service,
    provide_yandex_client,
)
from app.domain.auth.password_reset import PasswordResetService
from app.domain.auth.schemas import (
    LoginPayload,
    PasswordResetConfirmPayload,
    PasswordResetRequestPayload,
    RegisterPayload,
    SessionState,
    UserProfile,
)
from app.domain.auth.services import AuthService
from app.domain.auth.session import bind_user
from app.domain.auth.yandex import YandexOAuthClient
from app.lib.exceptions import ApplicationError, BadRequestError
from app.lib.request import AppRequest
from app.lib.security import constant_time_equals, generate_token
from app.lib.settings import get_settings

logger = logging.getLogger(__name__)

OAUTH_STATE_KEY = "oauth_state"
OAUTH_VERIFIER_KEY = "oauth_verifier"
OAUTH_NEXT_KEY = "oauth_next"


def _safe_next(path: str | None) -> str:
    if path and path.startswith("/") and not path.startswith("//"):
        return path
    return "/"


class AuthController(Controller):
    path = "/api/auth"
    tags = ["Auth"]
    dependencies = {
        "users_service": Provide(provide_users_service),
        "guest_mergers": Provide(provide_guest_mergers),
        "account_merge_service": Provide(provide_account_merge_service),
        "auth_service": Provide(provide_auth_service),
        "password_reset_service": Provide(provide_password_reset_service),
        "yandex_client": Provide(provide_yandex_client),
    }

    @get("/session", summary="Current session", description="Return the current user or null.")
    async def current_session(self, request: AppRequest) -> SessionState:
        user = request.user
        return SessionState(user=UserProfile.from_model(user) if user else None)

    @post(
        "/register",
        summary="Register",
        description="Create an account; an active guest session is upgraded in place.",
        middleware=[strict_rate_limit().middleware],
    )
    async def register(
        self,
        request: AppRequest,
        data: JSONBody[RegisterPayload],
        auth_service: NamedDependency[AuthService],
    ) -> UserProfile:
        user = await auth_service.register(data.email, data.password, data.display_name, request.user)
        bind_user(request, user)
        return UserProfile.from_model(user)

    @post(
        "/login",
        summary="Log in",
        description="Log in with email and password; guest progress is merged into the account.",
        status_code=HTTP_200_OK,
        middleware=[strict_rate_limit().middleware],
    )
    async def login(
        self,
        request: AppRequest,
        data: JSONBody[LoginPayload],
        auth_service: NamedDependency[AuthService],
    ) -> UserProfile:
        user = await auth_service.authenticate(data.email, data.password, request.user)
        bind_user(request, user)
        return UserProfile.from_model(user)

    @post("/logout", summary="Log out", description="Destroy the session.", status_code=HTTP_204_NO_CONTENT)
    async def logout(self, request: AppRequest) -> None:
        request.clear_session()

    @post(
        "/password-reset/request",
        summary="Request password reset",
        description="Send a reset link if the email belongs to an account. Always returns 202.",
        status_code=HTTP_202_ACCEPTED,
        middleware=[strict_rate_limit().middleware],
    )
    async def request_password_reset(
        self,
        data: JSONBody[PasswordResetRequestPayload],
        password_reset_service: NamedDependency[PasswordResetService],
    ) -> None:
        await password_reset_service.request_reset(data.email)

    @post(
        "/password-reset/confirm",
        summary="Confirm password reset",
        description="Set a new password using a reset token.",
        status_code=HTTP_204_NO_CONTENT,
        middleware=[strict_rate_limit().middleware],
    )
    async def confirm_password_reset(
        self,
        data: JSONBody[PasswordResetConfirmPayload],
        password_reset_service: NamedDependency[PasswordResetService],
    ) -> None:
        await password_reset_service.confirm_reset(data.token, data.password)

    @get(
        "/yandex/login",
        summary="Start Yandex ID login",
        description="Redirect to Yandex ID with state and PKCE challenge.",
    )
    async def yandex_login(
        self,
        request: AppRequest,
        yandex_client: NamedDependency[YandexOAuthClient],
        next_path: Annotated[str | None, QueryParameter(name="next")] = None,
    ) -> Redirect:
        state = generate_token()
        verifier = generate_token(48)
        request.set_session(
            {
                **request.session,
                OAUTH_STATE_KEY: state,
                OAUTH_VERIFIER_KEY: verifier,
                OAUTH_NEXT_KEY: _safe_next(next_path),
            }
        )
        return Redirect(yandex_client.authorize_url(state, verifier))

    @get(
        "/yandex/callback",
        summary="Yandex ID callback",
        description="Complete Yandex ID login and redirect back to the app.",
    )
    async def yandex_callback(
        self,
        request: AppRequest,
        yandex_client: NamedDependency[YandexOAuthClient],
        auth_service: NamedDependency[AuthService],
        code: FromQuery[str | None] = None,
        oauth_state: Annotated[str | None, QueryParameter(name="state")] = None,
    ) -> Response[None]:
        base_url = get_settings().public_base_url.rstrip("/")
        session = dict(request.session)
        expected_state = session.pop(OAUTH_STATE_KEY, None)
        verifier = session.pop(OAUTH_VERIFIER_KEY, None)
        next_path = _safe_next(session.pop(OAUTH_NEXT_KEY, None))
        request.set_session(session)
        try:
            if (
                not code
                or not oauth_state
                or not isinstance(expected_state, str)
                or not isinstance(verifier, str)
                or not constant_time_equals(oauth_state, expected_state)
            ):
                raise BadRequestError("OAuth state mismatch", code="oauth_failed")
            profile = await yandex_client.fetch_profile(code, verifier)
            user = await auth_service.login_with_yandex(profile, request.user)
        except ApplicationError as exc:
            logger.warning("Yandex login failed: %s", exc.detail)
            return Redirect(f"{base_url}/login?error={exc.code}")
        bind_user(request, user)
        return Redirect(f"{base_url}{next_path}")
