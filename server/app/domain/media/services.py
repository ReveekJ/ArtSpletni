from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from uuid_utils.compat import uuid7

from app.db.models import MediaAsset, MediaKind, MediaStatus
from app.domain.media.storage import ObjectStorage
from app.lib.exceptions import BadRequestError, NotFoundError

UPLOAD_TTL = timedelta(minutes=30)
PRIVATE_DOWNLOAD_TTL = timedelta(minutes=15)
PUBLIC_DOWNLOAD_TTL = timedelta(days=1)

_MB = 1024 * 1024


@dataclass(frozen=True, slots=True)
class MediaPolicy:
    max_bytes: int
    extensions: dict[str, str]


MEDIA_POLICIES: dict[MediaKind, MediaPolicy] = {
    MediaKind.IMAGE: MediaPolicy(
        max_bytes=15 * _MB,
        extensions={"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/avif": ".avif"},
    ),
    MediaKind.AUDIO: MediaPolicy(
        max_bytes=60 * _MB,
        extensions={
            "audio/mpeg": ".mp3",
            "audio/mp4": ".m4a",
            "audio/aac": ".aac",
            "audio/ogg": ".ogg",
            "audio/wav": ".wav",
            "audio/webm": ".weba",
        },
    ),
    MediaKind.VIDEO: MediaPolicy(
        max_bytes=300 * _MB,
        extensions={"video/mp4": ".mp4", "video/webm": ".webm", "video/quicktime": ".mov"},
    ),
}


@dataclass(frozen=True, slots=True)
class UploadTicket:
    asset: MediaAsset
    upload_url: str
    expires_at: datetime


class MediaRepository(SQLAlchemyAsyncRepository[MediaAsset]):
    model_type = MediaAsset


class MediaService:
    def __init__(self, repository: MediaRepository, storage: ObjectStorage) -> None:
        self._repository = repository
        self._storage = storage

    async def create_upload(
        self,
        *,
        kind: MediaKind,
        content_type: str,
        size_bytes: int,
        filename: str | None,
        is_public: bool,
        uploaded_by_id: UUID | None,
    ) -> UploadTicket:
        policy = MEDIA_POLICIES[kind]
        extension = policy.extensions.get(content_type)
        if extension is None:
            raise BadRequestError(f"Unsupported {kind} type: {content_type}", code="unsupported_media_type")
        if size_bytes <= 0 or size_bytes > policy.max_bytes:
            raise BadRequestError(f"{kind} must be at most {policy.max_bytes} bytes", code="media_too_large")
        visibility = "public" if is_public else "private"
        asset = await self._repository.add(
            MediaAsset(
                storage_key=f"{visibility}/{kind}/{uuid7()}{extension}",
                kind=kind,
                content_type=content_type,
                size_bytes=size_bytes,
                original_filename=filename,
                is_public=is_public,
                uploaded_by_id=uploaded_by_id,
            )
        )
        upload_url = await self._storage.presign_upload(asset.storage_key, UPLOAD_TTL)
        return UploadTicket(asset=asset, upload_url=upload_url, expires_at=datetime.now(UTC) + UPLOAD_TTL)

    async def complete_upload(self, asset_id: UUID) -> MediaAsset:
        asset = await self.get(asset_id)
        if asset.status is MediaStatus.READY:
            return asset
        actual_size = await self._storage.object_size(asset.storage_key)
        if actual_size is None:
            raise BadRequestError("File has not been uploaded yet", code="upload_missing")
        if actual_size > MEDIA_POLICIES[asset.kind].max_bytes:
            await self._storage.delete(asset.storage_key)
            raise BadRequestError("Uploaded file is too large", code="media_too_large")
        asset.size_bytes = actual_size
        asset.status = MediaStatus.READY
        return await self._repository.update(asset)

    async def get(self, asset_id: UUID) -> MediaAsset:
        asset = await self._repository.get_one_or_none(id=asset_id)
        if asset is None:
            raise NotFoundError("Media asset not found", code="media_not_found")
        return asset

    async def get_ready(self, asset_id: UUID, kind: MediaKind | None = None) -> MediaAsset:
        asset = await self.get(asset_id)
        if asset.status is not MediaStatus.READY:
            raise BadRequestError("Media upload is not completed", code="media_not_ready")
        if kind is not None and asset.kind is not kind:
            raise BadRequestError(f"Expected {kind} media", code="media_kind_mismatch")
        return asset

    async def get_many(self, asset_ids: set[UUID]) -> dict[UUID, MediaAsset]:
        if not asset_ids:
            return {}
        assets = await self._repository.get_many(MediaAsset.id.in_(asset_ids))
        return {asset.id: asset for asset in assets}

    async def download_url(self, asset: MediaAsset) -> str:
        ttl = PUBLIC_DOWNLOAD_TTL if asset.is_public else PRIVATE_DOWNLOAD_TTL
        return await self._storage.presign_download(asset.storage_key, ttl)

    async def delete(self, asset_id: UUID) -> None:
        asset = await self.get(asset_id)
        await self._repository.delete(asset.id)
        await self._storage.delete(asset.storage_key)
