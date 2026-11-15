from datetime import datetime
from typing import Annotated
from uuid import UUID

import msgspec

from app.db.models import Submission, SubmissionStatus
from app.domain.points.schemas import Latitude, Longitude
from app.lib.schema import CamelizedBaseStruct


class SubmissionInput(CamelizedBaseStruct):
    title: Annotated[str, msgspec.Meta(min_length=3, max_length=200)]
    story: Annotated[str, msgspec.Meta(min_length=20, max_length=10000)]
    latitude: Latitude
    longitude: Longitude
    asset_ids: Annotated[list[UUID], msgspec.Meta(max_length=5)] = msgspec.field(default_factory=list)


class RejectInput(CamelizedBaseStruct):
    comment: Annotated[str, msgspec.Meta(max_length=2000)] | None = None


class SubmissionOut(CamelizedBaseStruct):
    id: UUID
    title: str
    story: str
    language: str
    latitude: float
    longitude: float
    status: SubmissionStatus
    moderator_comment: str | None
    point_id: UUID | None
    asset_ids: list[UUID]
    created_at: datetime

    @classmethod
    def from_model(cls, submission: Submission) -> "SubmissionOut":
        return cls(
            id=submission.id,
            title=submission.title,
            story=submission.story,
            language=submission.language,
            latitude=submission.latitude,
            longitude=submission.longitude,
            status=submission.status,
            moderator_comment=submission.moderator_comment,
            point_id=submission.point_id,
            asset_ids=[item.asset_id for item in submission.media],
            created_at=submission.created_at,
        )


class AdminSubmissionOut(CamelizedBaseStruct):
    submission: SubmissionOut
    author_id: UUID
    author_email: str | None
