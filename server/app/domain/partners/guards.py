from uuid import UUID

from litestar.connection import ASGIConnection
from litestar.datastructures import State
from litestar.handlers.base import BaseRouteHandler

from app.config import alchemy_config
from app.db.models import User
from app.domain.partners.services import PartnerMemberRepository
from app.lib.exceptions import ForbiddenError, UnauthorizedError


async def requires_partner_member(
    connection: ASGIConnection[BaseRouteHandler, object, object, State], _: BaseRouteHandler
) -> None:
    user = connection.scope.get("user")
    if not isinstance(user, User) or user.is_guest:
        raise UnauthorizedError("Registered account required", code="registration_required")
    raw_partner_id = connection.path_params.get("partner_id")
    if not isinstance(raw_partner_id, UUID):
        raise ForbiddenError("Partner is not specified")
    if user.is_admin:
        return
    session = alchemy_config().provide_session(connection.app.state, connection.scope)
    member = await PartnerMemberRepository(session=session).get_one_or_none(
        partner_id=raw_partner_id, user_id=user.id
    )
    if member is None:
        raise ForbiddenError("You are not a member of this partner", code="not_partner_member")
