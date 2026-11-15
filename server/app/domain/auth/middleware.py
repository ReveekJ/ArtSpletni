from uuid import UUID

from litestar.connection import ASGIConnection
from litestar.datastructures import State
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult

from app.config import alchemy_config
from app.db.models import User
from app.domain.users.services import UserService

SESSION_USER_KEY = "uid"


class SessionUserMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(
        self, connection: ASGIConnection[object, object, object, State]
    ) -> AuthenticationResult:
        user = await self._load_user(connection)
        return AuthenticationResult(user=user, auth=None)

    async def _load_user(self, connection: ASGIConnection[object, object, object, State]) -> User | None:
        session = connection.scope.get("session")
        raw_id = session.get(SESSION_USER_KEY) if isinstance(session, dict) else None
        if not isinstance(raw_id, str):
            return None
        try:
            user_id = UUID(raw_id)
        except ValueError:
            connection.clear_session()
            return None
        db_session = alchemy_config().provide_session(connection.app.state, connection.scope)
        user = await UserService(session=db_session).get_one_or_none(id=user_id)
        if user is None or not user.is_active:
            connection.clear_session()
            return None
        return user
