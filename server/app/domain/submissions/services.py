import logging
from collections.abc import Sequence
from uuid import UUID

from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from app.db.models import (
    BlockKind,
    MediaKind,
    Point,
    PointKind,
    Submission,
    SubmissionMedia,
    SubmissionStatus,
    User,
)
from app.domain.i18n.services import TranslationService
from app.domain.media.services import MediaService
from app.domain.points.admin_service import PointAdminService
from app.domain.points.schemas import BlockInput, PointInput
from app.domain.submissions.schemas import SubmissionInput
from app.domain.users.services import UserService
from app.lib.exceptions import BadRequestError, ConflictError, NotFoundError, ServiceUnavailableError

logger = logging.getLogger(__name__)

SUBMISSION_MEDIA_BLOCKS: dict[MediaKind, BlockKind] = {
    MediaKind.IMAGE: BlockKind.IMAGE,
    MediaKind.AUDIO: BlockKind.AUDIO,
    MediaKind.VIDEO: BlockKind.VIDEO,
}


class SubmissionRepository(SQLAlchemyAsyncRepository[Submission]):
    model_type = Submission


class SubmissionService:
    def __init__(self, submissions: SubmissionRepository, media: MediaService) -> None:
        self._submissions = submissions
        self._media = media

    async def submit(self, user: User, data: SubmissionInput, language: str) -> Submission:
        media: list[SubmissionMedia] = []
        for position, asset_id in enumerate(dict.fromkeys(data.asset_ids)):
            asset = await self._media.get_ready(asset_id)
            if asset.uploaded_by_id != user.id:
                raise BadRequestError("Media belongs to another user", code="foreign_media")
            media.append(SubmissionMedia(asset_id=asset.id, position=position))
        return await self._submissions.add(
            Submission(
                user_id=user.id,
                title=data.title.strip(),
                story=data.story.strip(),
                language=language,
                latitude=data.latitude,
                longitude=data.longitude,
                media=media,
            )
        )

    async def mine(self, user_id: UUID) -> Sequence[Submission]:
        return await self._submissions.get_many(
            Submission.user_id == user_id, order_by=[(Submission.created_at, True)]
        )


class SubmissionModerationService:
    def __init__(
        self,
        submissions: SubmissionRepository,
        users: UserService,
        points: PointAdminService,
        media: MediaService,
        translator: TranslationService,
    ) -> None:
        self._submissions = submissions
        self._users = users
        self._points = points
        self._media = media
        self._translator = translator

    async def list_all(self, status: SubmissionStatus | None) -> Sequence[Submission]:
        filters = [Submission.status == status] if status else []
        return await self._submissions.get_many(*filters, order_by=[(Submission.created_at, True)])

    async def authors(self, submissions: Sequence[Submission]) -> dict[UUID, User]:
        user_ids = {item.user_id for item in submissions}
        if not user_ids:
            return {}
        return {user.id: user for user in await self._users.get_many(User.id.in_(user_ids))}

    async def get(self, submission_id: UUID) -> Submission:
        submission = await self._submissions.get_one_or_none(id=submission_id)
        if submission is None:
            raise NotFoundError("Submission not found", code="submission_not_found")
        return submission

    async def reject(self, submission_id: UUID, comment: str | None) -> Submission:
        submission = await self._pending(submission_id)
        submission.status = SubmissionStatus.REJECTED
        submission.moderator_comment = comment
        return await self._submissions.update(submission, auto_refresh=False)

    async def approve(self, submission_id: UUID) -> tuple[Submission, Point]:
        submission = await self._pending(submission_id)
        language, source = submission.language, self._translator.source_language
        blocks = [
            BlockInput(kind=BlockKind.TEXT, text=await self._to_source(submission.story, language, source))
        ]
        for item in submission.media:
            asset = await self._media.get(item.asset_id)
            blocks.append(BlockInput(kind=SUBMISSION_MEDIA_BLOCKS[asset.kind], asset_id=asset.id))
        point = await self._points.create(
            PointInput(
                kind=PointKind.GOSSIP,
                title=await self._to_source(submission.title, language, source),
                latitude=submission.latitude,
                longitude=submission.longitude,
                is_published=False,
                blocks=blocks,
            )
        )
        submission.status = SubmissionStatus.APPROVED
        submission.point_id = point.id
        return await self._submissions.update(submission, auto_refresh=False), point

    async def _to_source(self, text: str, language: str, source: str) -> dict[str, str]:
        if language == source:
            return {source: text}
        try:
            translated = await self._translator.translate_between(text, language, source)
        except ServiceUnavailableError:
            logger.warning("Could not translate submission text from %s; keeping original", language)
            return {source: text}
        return {language: text, source: translated}

    async def _pending(self, submission_id: UUID) -> Submission:
        submission = await self.get(submission_id)
        if submission.status is not SubmissionStatus.PENDING:
            raise ConflictError("Submission is already moderated", code="submission_moderated")
        return submission
