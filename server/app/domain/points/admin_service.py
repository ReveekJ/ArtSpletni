from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, or_, type_coerce
from sqlalchemy.dialects.postgresql import JSONB

from app.db.models import BlockKind, ContentBlock, ContentBlockMedia, MediaKind, Point, PointKind
from app.domain.i18n.services import TranslationService
from app.domain.media.services import MediaService
from app.domain.partners.services import PartnerRepository
from app.domain.points.repositories import PointRepository
from app.domain.points.schemas import BlockInput, PointInput
from app.lib.exceptions import BadRequestError, ConflictError, NotFoundError
from app.lib.i18n import LocalizedText

BLOCK_MEDIA_KIND: dict[BlockKind, MediaKind] = {
    BlockKind.IMAGE: MediaKind.IMAGE,
    BlockKind.AUDIO: MediaKind.AUDIO,
    BlockKind.VIDEO: MediaKind.VIDEO,
}


class PointAdminService:
    def __init__(
        self,
        points: PointRepository,
        partners: PartnerRepository,
        media: MediaService,
        translator: TranslationService,
    ) -> None:
        self._points = points
        self._partners = partners
        self._media = media
        self._translator = translator

    async def list_all(self, kind: PointKind | None = None, search: str | None = None) -> Sequence[Point]:
        filters: list[ColumnElement[bool]] = []
        if kind is not None:
            filters.append(Point.kind == kind)
        if search:
            pattern = f"%{search.strip()}%"
            title = type_coerce(Point.title, JSONB)
            filters.append(
                or_(*(title[lang]["text"].astext.ilike(pattern) for lang in self._translator.languages))
            )
        return await self._points.get_many(*filters, order_by=[(Point.updated_at, True)])

    async def get(self, point_id: UUID) -> Point:
        point = await self._points.get_one_or_none(id=point_id)
        if point is None:
            raise NotFoundError("Point not found", code="point_not_found")
        return point

    async def create(self, data: PointInput) -> Point:
        point = Point(kind=data.kind, title={}, latitude=data.latitude, longitude=data.longitude, blocks=[])
        await self._apply(point, data)
        return await self._points.add(point)

    async def update(self, point_id: UUID, data: PointInput) -> Point:
        point = await self.get(point_id)
        await self._apply(point, data)
        return await self._points.update(point, auto_refresh=False)

    async def delete(self, point_id: UUID) -> None:
        point = await self.get(point_id)
        if await self._points.route_usage_count(point.id):
            raise ConflictError("Point is used in a route", code="point_in_route")
        await self._points.delete(point.id)

    async def _apply(self, point: Point, data: PointInput) -> None:
        previous_blocks = list(point.blocks)
        title = await self._translator.localize(data.title, point.title or None)
        if title is None:
            raise BadRequestError("Title is required", code="title_required")
        point.title = title
        point.kind = data.kind
        point.latitude = data.latitude
        point.longitude = data.longitude
        point.address = await self._optional(data.address, point.address)
        point.note = await self._optional(data.note, point.note)
        point.is_published = data.is_published
        if data.partner_id is not None and await self._partners.get_one_or_none(id=data.partner_id) is None:
            raise NotFoundError("Partner not found", code="partner_not_found")
        point.partner_id = data.partner_id
        if data.cover_asset_id is not None:
            await self._media.get_ready(data.cover_asset_id, MediaKind.IMAGE)
        point.cover_asset_id = data.cover_asset_id
        point.blocks = [
            await self._build_block(
                index, block, previous_blocks[index] if index < len(previous_blocks) else None
            )
            for index, block in enumerate(data.blocks)
        ]
        self._validate_content(point)

    async def _optional(
        self, submitted: dict[str, str] | None, previous: LocalizedText | None
    ) -> LocalizedText | None:
        if submitted is None:
            return None
        return await self._translator.localize(submitted, previous, required=False)

    async def _build_block(
        self, position: int, data: BlockInput, previous: ContentBlock | None
    ) -> ContentBlock:
        same_kind = previous if previous is not None and previous.kind is data.kind else None
        block = ContentBlock(position=position, kind=data.kind)
        if data.kind is BlockKind.TEXT:
            if data.asset_id is not None or data.media_variants:
                raise BadRequestError("Text blocks cannot carry media", code="invalid_block")
            block.text = await self._translator.localize(
                data.text or {}, same_kind.text if same_kind else None
            )
            return block
        media_kind = BLOCK_MEDIA_KIND[data.kind]
        if data.asset_id is None:
            raise BadRequestError(f"{data.kind} block requires media", code="invalid_block")
        await self._media.get_ready(data.asset_id, media_kind)
        block.asset_id = data.asset_id
        block.caption = await self._optional(data.caption, same_kind.caption if same_kind else None)
        if data.transcript is not None and data.kind is not BlockKind.AUDIO:
            raise BadRequestError("Only audio blocks can carry a transcript", code="invalid_block")
        block.transcript = await self._optional(data.transcript, same_kind.transcript if same_kind else None)
        variants: list[ContentBlockMedia] = []
        for language, asset_id in data.media_variants.items():
            if language not in self._translator.languages:
                raise BadRequestError(f"Unsupported language {language}", code="unsupported_language")
            await self._media.get_ready(asset_id, media_kind)
            variants.append(ContentBlockMedia(language=language, asset_id=asset_id))
        block.media_variants = variants
        return block

    @staticmethod
    def _validate_content(point: Point) -> None:
        if point.kind is PointKind.GOSSIP and not point.blocks:
            raise BadRequestError("Gossip point needs at least one content block", code="content_required")
        if point.kind is PointKind.PARTNER and point.partner_id is None:
            raise BadRequestError("Partner point must reference a partner", code="partner_required")
        if point.kind is PointKind.GOSSIP and point.partner_id is not None:
            raise BadRequestError("Gossip points cannot belong to a partner", code="unexpected_partner")
