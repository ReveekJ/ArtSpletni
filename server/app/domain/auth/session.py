from app.db.models import User
from app.domain.auth.middleware import SESSION_USER_KEY
from app.lib.request import AppRequest


def bind_user(request: AppRequest, user: User) -> None:
    request.set_session({SESSION_USER_KEY: str(user.id)})
    request.scope["user"] = user
