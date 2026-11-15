from uuid import UUID

from litestar import Controller, delete, get, post, put
from litestar.di import NamedDependency, Provide
from litestar.params import FromPath, FromQuery, JSONBody
from litestar.status_codes import HTTP_200_OK

from app.db.models import PointKind
from app.domain.auth.guards import requires_actor, requires_admin
from app.domain.nfc.deps import provide_nfc_tag_service
from app.domain.nfc.schemas import IssuedTagOut, IssueTagInput, NfcTagOut
from app.domain.nfc.services import NfcTagService
from app.domain.points.admin_service import PointAdminService
from app.domain.points.content_service import PointContentService
from app.domain.points.deps import provide_point_admin_service, provide_point_content_service
from app.domain.points.mappers import admin_point_out, admin_point_summary
from app.domain.points.schemas import (
    AdminPointOut,
    AdminPointSummary,
    CollectionItem,
    PointContentOut,
    PointInput,
)
from app.lib.request import AppRequest, require_user


class AdminPointController(Controller):
    path = "/api/admin/points"
    tags = ["Admin: Points"]
    guards = [requires_admin]
    dependencies = {
        "point_admin_service": Provide(provide_point_admin_service),
        "nfc_tag_service": Provide(provide_nfc_tag_service),
    }

    @get("/", summary="List points", description="List points with optional kind filter and title search.")
    async def list_points(
        self,
        point_admin_service: NamedDependency[PointAdminService],
        kind: FromQuery[PointKind | None] = None,
        search: FromQuery[str | None] = None,
    ) -> list[AdminPointSummary]:
        return [admin_point_summary(point) for point in await point_admin_service.list_all(kind, search)]

    @post("/", summary="Create point", description="Create a point; missing translations are machine-filled.")
    async def create_point(
        self, data: JSONBody[PointInput], point_admin_service: NamedDependency[PointAdminService]
    ) -> AdminPointOut:
        return admin_point_out(await point_admin_service.create(data))

    @get(
        "/{point_id:uuid}",
        summary="Get point",
        description="Return a point with all translations and blocks.",
    )
    async def get_point(
        self, point_id: FromPath[UUID], point_admin_service: NamedDependency[PointAdminService]
    ) -> AdminPointOut:
        return admin_point_out(await point_admin_service.get(point_id))

    @put("/{point_id:uuid}", summary="Update point", description="Replace point fields and content blocks.")
    async def update_point(
        self,
        point_id: FromPath[UUID],
        data: JSONBody[PointInput],
        point_admin_service: NamedDependency[PointAdminService],
    ) -> AdminPointOut:
        return admin_point_out(await point_admin_service.update(point_id, data))

    @delete(
        "/{point_id:uuid}",
        summary="Delete point",
        description="Delete a point that is not used by any route.",
    )
    async def delete_point(
        self, point_id: FromPath[UUID], point_admin_service: NamedDependency[PointAdminService]
    ) -> None:
        await point_admin_service.delete(point_id)

    @get("/{point_id:uuid}/tags", summary="List NFC tags", description="List NFC tags issued for a point.")
    async def list_tags(
        self,
        point_id: FromPath[UUID],
        point_admin_service: NamedDependency[PointAdminService],
        nfc_tag_service: NamedDependency[NfcTagService],
    ) -> list[NfcTagOut]:
        await point_admin_service.get(point_id)
        return [NfcTagOut.from_model(tag) for tag in await nfc_tag_service.list_for_point(point_id)]

    @post(
        "/{point_id:uuid}/tags",
        summary="Issue NFC tag",
        description="Issue a new tag secret; the URL is returned only once and must be written to the tag.",
    )
    async def issue_tag(
        self,
        point_id: FromPath[UUID],
        data: JSONBody[IssueTagInput],
        point_admin_service: NamedDependency[PointAdminService],
        nfc_tag_service: NamedDependency[NfcTagService],
    ) -> IssuedTagOut:
        await point_admin_service.get(point_id)
        issued = await nfc_tag_service.issue(point_id, data.label)
        return IssuedTagOut(tag=NfcTagOut.from_model(issued.tag), url=issued.url)


class AdminTagController(Controller):
    path = "/api/admin/tags"
    tags = ["Admin: Points"]
    guards = [requires_admin]
    dependencies = {"nfc_tag_service": Provide(provide_nfc_tag_service)}

    @post(
        "/{tag_id:uuid}/revoke",
        summary="Revoke NFC tag",
        description="Revoke a tag; scans of it stop working.",
        status_code=HTTP_200_OK,
    )
    async def revoke_tag(
        self, tag_id: FromPath[UUID], nfc_tag_service: NamedDependency[NfcTagService]
    ) -> NfcTagOut:
        return NfcTagOut.from_model(await nfc_tag_service.revoke(tag_id))


class PointController(Controller):
    path = "/api/points"
    tags = ["Points"]
    guards = [requires_actor]
    dependencies = {"point_content_service": Provide(provide_point_content_service)}

    @get(
        "/{point_id:uuid}",
        summary="Point content",
        description="Return point content; available only after the point was unlocked by an NFC scan.",
    )
    async def get_content(
        self,
        request: AppRequest,
        point_id: FromPath[UUID],
        point_content_service: NamedDependency[PointContentService],
    ) -> PointContentOut:
        return await point_content_service.content(require_user(request).id, point_id)


class CollectionController(Controller):
    path = "/api/me/collection"
    tags = ["Me"]
    guards = [requires_actor]
    dependencies = {"point_content_service": Provide(provide_point_content_service)}

    @get("/", summary="My collection", description="Points the current user has unlocked, newest first.")
    async def collection(
        self, request: AppRequest, point_content_service: NamedDependency[PointContentService]
    ) -> list[CollectionItem]:
        return await point_content_service.collection(require_user(request).id)
