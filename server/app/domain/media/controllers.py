from uuid import UUID

from litestar import Controller, delete, get, post
from litestar.di import NamedDependency
from litestar.params import FromPath, JSONBody
from litestar.status_codes import HTTP_200_OK

from app.domain.auth.guards import requires_admin
from app.domain.media.schemas import MediaAssetOut, UploadRequest, UploadTicketOut
from app.domain.media.services import MediaService
from app.lib.request import AppRequest


class AdminMediaController(Controller):
    path = "/api/admin/media"
    tags = ["Admin: Media"]
    guards = [requires_admin]

    @post(
        "/uploads",
        summary="Start media upload",
        description="Register a media asset and return a presigned PUT URL for direct upload.",
    )
    async def start_upload(
        self,
        request: AppRequest,
        data: JSONBody[UploadRequest],
        media_service: NamedDependency[MediaService],
    ) -> UploadTicketOut:
        ticket = await media_service.create_upload(
            kind=data.kind,
            content_type=data.content_type,
            size_bytes=data.size_bytes,
            filename=data.filename,
            is_public=data.is_public,
            uploaded_by_id=request.user.id if request.user else None,
        )
        return UploadTicketOut(
            asset=MediaAssetOut.from_model(ticket.asset),
            upload_url=ticket.upload_url,
            expires_at=ticket.expires_at,
        )

    @post(
        "/{asset_id:uuid}/complete",
        summary="Complete media upload",
        description="Verify the uploaded object and mark the asset as ready.",
        status_code=HTTP_200_OK,
    )
    async def complete_upload(
        self, asset_id: FromPath[UUID], media_service: NamedDependency[MediaService]
    ) -> MediaAssetOut:
        asset = await media_service.complete_upload(asset_id)
        return MediaAssetOut.from_model(asset, await media_service.download_url(asset))

    @get(
        "/{asset_id:uuid}", summary="Get media asset", description="Return asset metadata and a download URL."
    )
    async def get_asset(
        self, asset_id: FromPath[UUID], media_service: NamedDependency[MediaService]
    ) -> MediaAssetOut:
        asset = await media_service.get(asset_id)
        return MediaAssetOut.from_model(asset, await media_service.download_url(asset))

    @delete(
        "/{asset_id:uuid}", summary="Delete media asset", description="Delete the asset and its stored file."
    )
    async def delete_asset(
        self, asset_id: FromPath[UUID], media_service: NamedDependency[MediaService]
    ) -> None:
        await media_service.delete(asset_id)
