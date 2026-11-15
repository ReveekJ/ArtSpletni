from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from app.db.models import NfcTag
from app.lib.exceptions import NotFoundError
from app.lib.security import generate_token, hash_token


class NfcTagRepository(SQLAlchemyAsyncRepository[NfcTag]):
    model_type = NfcTag


@dataclass(frozen=True, slots=True)
class IssuedTag:
    tag: NfcTag
    url: str


class NfcTagService:
    def __init__(self, tags: NfcTagRepository, public_base_url: str) -> None:
        self._tags = tags
        self._base_url = public_base_url.rstrip("/")

    async def issue(self, point_id: UUID, label: str | None) -> IssuedTag:
        token = generate_token()
        tag = await self._tags.add(NfcTag(point_id=point_id, token_hash=hash_token(token), label=label))
        return IssuedTag(tag=tag, url=f"{self._base_url}/s/{token}")

    async def list_for_point(self, point_id: UUID) -> Sequence[NfcTag]:
        return await self._tags.get_many(NfcTag.point_id == point_id, order_by=[(NfcTag.created_at, False)])

    async def revoke(self, tag_id: UUID) -> NfcTag:
        tag = await self._tags.get_one_or_none(id=tag_id)
        if tag is None:
            raise NotFoundError("Tag not found", code="tag_not_found")
        if tag.revoked_at is None:
            tag.revoked_at = datetime.now(UTC)
            tag = await self._tags.update(tag)
        return tag

    async def resolve(self, token: str) -> NfcTag | None:
        tag = await self._tags.get_one_or_none(token_hash=hash_token(token))
        if tag is None or tag.revoked_at is not None:
            return None
        tag.last_scanned_at = datetime.now(UTC)
        return await self._tags.update(tag)
