from datetime import datetime
from typing import Annotated
from uuid import UUID

import msgspec

from app.db.models import MediaAsset, MediaKind, MediaStatus
from app.lib.schema import CamelizedBaseStruct


class UploadRequest(CamelizedBaseStruct):
    kind: MediaKind
    content_type: Annotated[str, msgspec.Meta(max_length=128)]
    size_bytes: Annotated[int, msgspec.Meta(gt=0)]
    filename: Annotated[str, msgspec.Meta(max_length=255)] | None = None
    is_public: bool = False


class MediaAssetOut(CamelizedBaseStruct):
    id: UUID
    kind: MediaKind
    content_type: str
    size_bytes: int
    original_filename: str | None
    is_public: bool
    status: MediaStatus
    url: str | None = None

    @classmethod
    def from_model(cls, asset: MediaAsset, url: str | None = None) -> "MediaAssetOut":
        return cls(
            id=asset.id,
            kind=asset.kind,
            content_type=asset.content_type,
            size_bytes=asset.size_bytes,
            original_filename=asset.original_filename,
            is_public=asset.is_public,
            status=asset.status,
            url=url,
        )


class UploadTicketOut(CamelizedBaseStruct):
    asset: MediaAssetOut
    upload_url: str
    expires_at: datetime
