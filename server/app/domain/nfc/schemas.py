from datetime import datetime
from typing import Annotated
from uuid import UUID

import msgspec

from app.db.models import NfcTag
from app.lib.schema import CamelizedBaseStruct


class IssueTagInput(CamelizedBaseStruct):
    label: Annotated[str, msgspec.Meta(max_length=120)] | None = None


class NfcTagOut(CamelizedBaseStruct):
    id: UUID
    point_id: UUID
    label: str | None
    revoked_at: datetime | None
    last_scanned_at: datetime | None
    created_at: datetime

    @classmethod
    def from_model(cls, tag: NfcTag) -> "NfcTagOut":
        return cls(
            id=tag.id,
            point_id=tag.point_id,
            label=tag.label,
            revoked_at=tag.revoked_at,
            last_scanned_at=tag.last_scanned_at,
            created_at=tag.created_at,
        )


class IssuedTagOut(CamelizedBaseStruct):
    tag: NfcTagOut
    url: str
