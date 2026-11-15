from uuid import UUID

from litestar import Controller, get, post
from litestar.di import NamedDependency, Provide
from litestar.params import FromPath, FromQuery, JSONBody
from litestar.status_codes import HTTP_200_OK
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import rate_limit
from app.db.models import SubmissionStatus
from app.domain.auth.guards import requires_admin, requires_registered
from app.domain.i18n.services import TranslationService
from app.domain.media.schemas import MediaAssetOut, UploadRequest, UploadTicketOut
from app.domain.media.services import MediaService
from app.domain.points.admin_service import PointAdminService
from app.domain.points.deps import provide_point_admin_service
from app.domain.submissions.schemas import AdminSubmissionOut, RejectInput, SubmissionInput, SubmissionOut
from app.domain.submissions.services import (
    SubmissionModerationService,
    SubmissionRepository,
    SubmissionService,
)
from app.domain.users.services import UserService
from app.lib.exceptions import ForbiddenError
from app.lib.request import AppRequest, require_user

SUBMISSION_RATE_LIMIT = rate_limit("submission", "hour", 5)
UPLOAD_RATE_LIMIT = rate_limit("upload", "hour", 30)


async def provide_submission_service(
    db_session: NamedDependency[AsyncSession], media_service: NamedDependency[MediaService]
) -> SubmissionService:
    return SubmissionService(SubmissionRepository(session=db_session), media_service)


async def provide_moderation_service(
    db_session: NamedDependency[AsyncSession],
    point_admin_service: NamedDependency[PointAdminService],
    media_service: NamedDependency[MediaService],
    translation_service: NamedDependency[TranslationService],
) -> SubmissionModerationService:
    return SubmissionModerationService(
        SubmissionRepository(session=db_session),
        UserService(session=db_session),
        point_admin_service,
        media_service,
        translation_service,
    )


class MySubmissionsController(Controller):
    path = "/api/me"
    tags = ["Submissions"]
    guards = [requires_registered]
    dependencies = {"submission_service": Provide(provide_submission_service)}

    @post(
        "/media/uploads",
        summary="Upload media for a submission",
        description="Register a private media upload owned by the current user.",
        middleware=[UPLOAD_RATE_LIMIT.middleware],
    )
    async def start_upload(
        self, request: AppRequest, data: JSONBody[UploadRequest], media_service: NamedDependency[MediaService]
    ) -> UploadTicketOut:
        ticket = await media_service.create_upload(
            kind=data.kind,
            content_type=data.content_type,
            size_bytes=data.size_bytes,
            filename=data.filename,
            is_public=False,
            uploaded_by_id=require_user(request).id,
        )
        return UploadTicketOut(
            asset=MediaAssetOut.from_model(ticket.asset),
            upload_url=ticket.upload_url,
            expires_at=ticket.expires_at,
        )

    @post(
        "/media/{asset_id:uuid}/complete",
        summary="Complete own upload",
        description="Verify an uploaded file owned by the current user.",
        status_code=HTTP_200_OK,
    )
    async def complete_upload(
        self, request: AppRequest, asset_id: FromPath[UUID], media_service: NamedDependency[MediaService]
    ) -> MediaAssetOut:
        asset = await media_service.get(asset_id)
        if asset.uploaded_by_id != require_user(request).id:
            raise ForbiddenError("Not your upload", code="foreign_media")
        return MediaAssetOut.from_model(await media_service.complete_upload(asset_id))

    @post(
        "/submissions",
        summary="Suggest a gossip",
        description="Submit a story with a location for moderation.",
        middleware=[SUBMISSION_RATE_LIMIT.middleware],
    )
    async def submit(
        self,
        request: AppRequest,
        data: JSONBody[SubmissionInput],
        language: NamedDependency[str],
        submission_service: NamedDependency[SubmissionService],
    ) -> SubmissionOut:
        return SubmissionOut.from_model(
            await submission_service.submit(require_user(request), data, language)
        )

    @get("/submissions", summary="My submissions", description="Stories submitted by the current user.")
    async def mine(
        self, request: AppRequest, submission_service: NamedDependency[SubmissionService]
    ) -> list[SubmissionOut]:
        return [
            SubmissionOut.from_model(item) for item in await submission_service.mine(require_user(request).id)
        ]


class AdminSubmissionController(Controller):
    path = "/api/admin/submissions"
    tags = ["Admin: Moderation"]
    guards = [requires_admin]
    dependencies = {
        "point_admin_service": Provide(provide_point_admin_service),
        "moderation_service": Provide(provide_moderation_service),
    }

    @get("/", summary="List submissions", description="Submitted stories, optionally filtered by status.")
    async def list_submissions(
        self,
        moderation_service: NamedDependency[SubmissionModerationService],
        status: FromQuery[SubmissionStatus | None] = SubmissionStatus.PENDING,
    ) -> list[AdminSubmissionOut]:
        submissions = await moderation_service.list_all(status)
        authors = await moderation_service.authors(submissions)
        return [
            AdminSubmissionOut(
                submission=SubmissionOut.from_model(item),
                author_id=item.user_id,
                author_email=authors[item.user_id].email if item.user_id in authors else None,
            )
            for item in submissions
        ]

    @post(
        "/{submission_id:uuid}/approve",
        summary="Approve submission",
        description="Create an unpublished draft point from the submission for editing.",
        status_code=HTTP_200_OK,
    )
    async def approve(
        self, submission_id: FromPath[UUID], moderation_service: NamedDependency[SubmissionModerationService]
    ) -> SubmissionOut:
        submission, _ = await moderation_service.approve(submission_id)
        return SubmissionOut.from_model(submission)

    @post(
        "/{submission_id:uuid}/reject",
        summary="Reject submission",
        description="Reject a submission with an optional comment for the author.",
        status_code=HTTP_200_OK,
    )
    async def reject(
        self,
        submission_id: FromPath[UUID],
        data: JSONBody[RejectInput],
        moderation_service: NamedDependency[SubmissionModerationService],
    ) -> SubmissionOut:
        return SubmissionOut.from_model(await moderation_service.reject(submission_id, data.comment))
