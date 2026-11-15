from litestar import Request
from litestar.datastructures import State

from app.db.models import User
from app.lib.exceptions import UnauthorizedError

AppRequest = Request[User | None, None, State]


def require_user(request: AppRequest) -> User:
    if request.user is None:
        raise UnauthorizedError("Authentication required")
    return request.user
