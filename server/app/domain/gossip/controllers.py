from uuid import UUID

from litestar import Controller, Response, get, patch, post
from litestar.di import NamedDependency, Provide
from litestar.params import FromPath, JSONBody
from litestar.status_codes import HTTP_200_OK, HTTP_202_ACCEPTED

from app.domain.auth.guards import requires_actor, requires_admin
from app.domain.gossip.deps import provide_gossip_service
from app.domain.gossip.schemas import (
    AdminGossipFeedOut,
    AdminGossipItemOut,
    GossipFeedOut,
    GossipHiddenInput,
    GossipRegenerateOut,
)
from app.domain.gossip.service import GossipService
from app.domain.gossip.tasks import background_for
from app.lib.request import AppRequest, require_user


class PointGossipController(Controller):
    path = "/api/points/{point_id:uuid}/gossip"
    tags = ["Points"]
    guards = [requires_actor]
    dependencies = {"gossip_service": Provide(provide_gossip_service)}

    @get(
        "/",
        summary="Nearby gossip",
        description=(
            "LLM-written stories about the point surroundings in the requested language. "
            "Available only after the point was unlocked; the first call starts generation in the background. "
            "Stories may be untrue: each one carries a veracity label."
        ),
    )
    async def get_feed(
        self,
        request: AppRequest,
        point_id: FromPath[UUID],
        gossip_service: NamedDependency[GossipService],
    ) -> Response[GossipFeedOut]:
        result = await gossip_service.feed(require_user(request).id, point_id)
        return Response(result.feed, background=background_for(result.task))


class AdminGossipController(Controller):
    path = "/api/admin"
    tags = ["Admin: Gossip"]
    guards = [requires_admin]
    dependencies = {"gossip_service": Provide(provide_gossip_service)}

    @get(
        "/points/{point_id:uuid}/gossip",
        summary="Point gossip (admin)",
        description="Generation status and all stories of a point, including hidden ones, with translations.",
    )
    async def get_admin_feed(
        self, point_id: FromPath[UUID], gossip_service: NamedDependency[GossipService]
    ) -> AdminGossipFeedOut:
        return await gossip_service.admin_feed(point_id)

    @post(
        "/points/{point_id:uuid}/gossip/regenerate",
        summary="Regenerate gossip",
        description="Queue gossip regeneration for a point; previous stories stay until the new ones are ready.",
        status_code=HTTP_202_ACCEPTED,
    )
    async def regenerate(
        self, point_id: FromPath[UUID], gossip_service: NamedDependency[GossipService]
    ) -> Response[GossipRegenerateOut]:
        result = await gossip_service.regenerate(point_id)
        return Response(result.status, status_code=HTTP_202_ACCEPTED, background=background_for(result.task))

    @patch(
        "/gossip/{item_id:uuid}",
        summary="Hide or show a story",
        description="Hidden stories are not shown to players.",
        status_code=HTTP_200_OK,
    )
    async def set_hidden(
        self,
        item_id: FromPath[UUID],
        data: JSONBody[GossipHiddenInput],
        gossip_service: NamedDependency[GossipService],
    ) -> AdminGossipItemOut:
        return await gossip_service.set_hidden(item_id, data.is_hidden)
