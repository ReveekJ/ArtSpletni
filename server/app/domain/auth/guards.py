from litestar.connection import ASGIConnection
from litestar.datastructures import State
from litestar.handlers.base import BaseRouteHandler

from app.db.models import User
from app.lib.exceptions import ForbiddenError, UnauthorizedError


def _user(connection: ASGIConnection[BaseRouteHandler, object, object, State]) -> User | None:
    user = connection.scope.get("user")
    return user if isinstance(user, User) else None


def requires_actor(
    connection: ASGIConnection[BaseRouteHandler, object, object, State], _: BaseRouteHandler
) -> None:
    if _user(connection) is None:
        raise UnauthorizedError("Authentication required")


def requires_registered(
    connection: ASGIConnection[BaseRouteHandler, object, object, State], _: BaseRouteHandler
) -> None:
    user = _user(connection)
    if user is None or user.is_guest:
        raise UnauthorizedError("Registered account required", code="registration_required")


def requires_admin(
    connection: ASGIConnection[BaseRouteHandler, object, object, State], _: BaseRouteHandler
) -> None:
    user = _user(connection)
    if user is None:
        raise UnauthorizedError("Authentication required")
    if not user.is_admin:
        raise ForbiddenError("Administrator role required")
