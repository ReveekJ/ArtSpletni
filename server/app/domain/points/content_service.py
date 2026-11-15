from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from app.db.models import ContentBlock, MediaAsset, Point
from app.domain.media.services import MediaService
from app.domain.points.repositories import PointRepository, UnlockRepository
from app.domain.points.schemas import BlockOut, CollectionItem, PointCard, PointContentOut
from app.lib.exceptions import ForbiddenError, NotFoundError
from app.lib.i18n import resolve_text


class PointContentService:
    def __init__(
        self,
        points: PointRepository,
        unlocks: UnlockRepository,
        media: MediaService,
        language: str,
        fallback_language: str,
    ) -> None:
        self._points = points
        self._unlocks = unlocks
        self._media = media
        self._language = language
        self._fallback = fallback_language

    async def content(self, user_id: UUID, point_id: UUID) -> PointContentOut:
        unlock = await self._unlocks.get_one_or_none(user_id=user_id, point_id=point_id)
        if unlock is None:
            raise ForbiddenError("Scan the NFC tag to unlock this point", code="point_locked")
        point = await self._points.get_one_or_none(id=point_id)
        if point is None:
            raise NotFoundError("Point not found", code="point_not_found")
        return await self.render(point, unlock.created_at)

    async def render(self, point: Point, unlocked_at: datetime) -> PointContentOut:
        assets = await self._media.get_many(self._asset_ids(point))
        blocks = [await self._render_block(block, assets) for block in point.blocks]
        return PointContentOut(
            id=point.id,
            kind=point.kind,
            title=resolve_text(point.title, self._language, self._fallback) or "",
            address=resolve_text(point.address, self._language, self._fallback),
            note=resolve_text(point.note, self._language, self._fallback),
            latitude=point.latitude,
            longitude=point.longitude,
            cover_url=await self._url(point.cover_asset_id, assets),
            blocks=blocks,
            unlocked_at=unlocked_at,
        )

    async def cards(self, points: Sequence[Point]) -> dict[UUID, PointCard]:
        cover_ids = {point.cover_asset_id for point in points if point.cover_asset_id is not None}
        assets = await self._media.get_many(cover_ids)
        return {
            point.id: PointCard(
                id=point.id,
                kind=point.kind,
                title=resolve_text(point.title, self._language, self._fallback) or "",
                cover_url=await self._url(point.cover_asset_id, assets),
            )
            for point in points
        }

    async def collection(self, user_id: UUID) -> list[CollectionItem]:
        unlocks = await self._unlocks.for_user(user_id)
        points = await self._points.get_many(Point.id.in_([unlock.point_id for unlock in unlocks]))
        cards = await self.cards(points)
        return [
            CollectionItem(point=cards[unlock.point_id], unlocked_at=unlock.created_at)
            for unlock in unlocks
            if unlock.point_id in cards
        ]

    async def _render_block(self, block: ContentBlock, assets: dict[UUID, MediaAsset]) -> BlockOut:
        asset_id = self._block_asset_id(block)
        asset = assets.get(asset_id) if asset_id is not None else None
        return BlockOut(
            kind=block.kind,
            text=resolve_text(block.text, self._language, self._fallback),
            caption=resolve_text(block.caption, self._language, self._fallback),
            transcript=resolve_text(block.transcript, self._language, self._fallback),
            asset_id=asset.id if asset is not None else None,
            media_url=await self._media.download_url(asset) if asset is not None else None,
            content_type=asset.content_type if asset is not None else None,
        )

    def _block_asset_id(self, block: ContentBlock) -> UUID | None:
        variants = {variant.language: variant.asset_id for variant in block.media_variants}
        return variants.get(self._language) or block.asset_id

    def _asset_ids(self, point: Point) -> set[UUID]:
        ids = {point.cover_asset_id} if point.cover_asset_id is not None else set()
        for block in point.blocks:
            asset_id = self._block_asset_id(block)
            if asset_id is not None:
                ids.add(asset_id)
        return ids

    async def _url(self, asset_id: UUID | None, assets: dict[UUID, MediaAsset]) -> str | None:
        asset = assets.get(asset_id) if asset_id is not None else None
        return await self._media.download_url(asset) if asset is not None else None
