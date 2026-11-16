from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.db.models import GossipGeneration, GossipStatus, Point
from app.domain.gossip.generation import ACTIVE_STATUSES
from app.domain.gossip.mappers import admin_gossip_item_out, gossip_item_out
from app.domain.gossip.repositories import GossipGenerationRepository, GossipItemRepository
from app.domain.gossip.schemas import (
    AdminGossipFeedOut,
    AdminGossipItemOut,
    GossipFeedOut,
    GossipRegenerateOut,
)
from app.domain.points.repositories import PointRepository, UnlockRepository
from app.lib.exceptions import ForbiddenError, NotFoundError, ServiceUnavailableError


@dataclass(frozen=True, slots=True)
class GenerationTask:
    point_id: UUID
    attempt_id: UUID


@dataclass(frozen=True, slots=True)
class FeedResult:
    feed: GossipFeedOut
    task: GenerationTask | None


@dataclass(frozen=True, slots=True)
class RegenerateResult:
    status: GossipRegenerateOut
    task: GenerationTask | None


class GossipService:
    def __init__(
        self,
        generations: GossipGenerationRepository,
        items: GossipItemRepository,
        points: PointRepository,
        unlocks: UnlockRepository,
        language: str,
        fallback_language: str,
        enabled: bool,
        stale_after: timedelta,
        failed_retry_after: timedelta,
    ) -> None:
        self._generations = generations
        self._items = items
        self._points = points
        self._unlocks = unlocks
        self._language = language
        self._fallback = fallback_language
        self._enabled = enabled
        self._stale_after = stale_after
        self._failed_retry_after = failed_retry_after

    async def feed(self, user_id: UUID, point_id: UUID) -> FeedResult:
        if await self._unlocks.get_one_or_none(user_id=user_id, point_id=point_id) is None:
            raise ForbiddenError("Scan the NFC tag to unlock this point", code="point_locked")
        point = await self._get_point(point_id)
        generation = await self._generations.get_one_or_none(point_id=point_id)
        task = (
            await self._claim(point, generation)
            if self._enabled and self._needs_run(point, generation)
            else None
        )
        if task is not None:
            generation = await self._generations.get_one_or_none(point_id=point_id)
        items = await self._items.for_point(point_id, include_hidden=False)
        return FeedResult(
            feed=GossipFeedOut(
                status=generation.status if generation else GossipStatus.NONE,
                items=[gossip_item_out(item, self._language, self._fallback) for item in items],
            ),
            task=task,
        )

    async def admin_feed(self, point_id: UUID) -> AdminGossipFeedOut:
        await self._get_point(point_id)
        generation = await self._generations.get_one_or_none(point_id=point_id)
        items = await self._items.for_point(point_id, include_hidden=True)
        return AdminGossipFeedOut(
            status=generation.status if generation else GossipStatus.NONE,
            enabled=self._enabled,
            error=generation.error if generation else None,
            finished_at=generation.finished_at if generation else None,
            items=[admin_gossip_item_out(item, self._language, self._fallback) for item in items],
        )

    async def regenerate(self, point_id: UUID) -> RegenerateResult:
        if not self._enabled:
            raise ServiceUnavailableError("LLM is not configured", code="llm_not_configured")
        point = await self._get_point(point_id)
        generation = await self._generations.get_one_or_none(point_id=point_id)
        task = await self._claim(point, generation)
        generation = await self._generations.get_one_or_none(point_id=point_id)
        status = generation.status if generation else GossipStatus.NONE
        return RegenerateResult(status=GossipRegenerateOut(status=status), task=task)

    async def set_hidden(self, item_id: UUID, is_hidden: bool) -> AdminGossipItemOut:
        item = await self._items.get_one_or_none(id=item_id)
        if item is None:
            raise NotFoundError("Gossip item not found", code="gossip_item_not_found")
        item.is_hidden = is_hidden
        item = await self._items.update(item, auto_refresh=False)
        return admin_gossip_item_out(item, self._language, self._fallback)

    async def _get_point(self, point_id: UUID) -> Point:
        point = await self._points.get_one_or_none(id=point_id)
        if point is None:
            raise NotFoundError("Point not found", code="point_not_found")
        return point

    async def _claim(self, point: Point, generation: GossipGeneration | None) -> GenerationTask | None:
        if generation is None:
            claimed = await self._generations.create_pending(point.id, point.latitude, point.longitude)
        else:
            claimed = await self._generations.restart(generation, point.latitude, point.longitude)
        if claimed is None:
            return None
        return GenerationTask(point_id=point.id, attempt_id=claimed.attempt_id)

    def _needs_run(self, point: Point, generation: GossipGeneration | None) -> bool:
        if generation is None:
            return True
        if (generation.latitude, generation.longitude) != (point.latitude, point.longitude):
            return True
        now = datetime.now(UTC)
        if generation.status in ACTIVE_STATUSES:
            return now - generation.updated_at > self._stale_after
        if generation.status is GossipStatus.FAILED:
            return now - (generation.finished_at or generation.updated_at) > self._failed_retry_after
        return False
