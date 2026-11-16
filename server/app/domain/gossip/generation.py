import logging
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    GossipGeneration,
    GossipItem,
    GossipSource,
    GossipSourceOrigin,
    GossipStatus,
    GossipVeracity,
    Point,
)
from app.domain.gossip.llm_schema import LlmGossipItem, LlmGossipResponse, LlmText
from app.domain.gossip.protocols import GossipWriter, LinkChecker, NearbySource
from app.domain.gossip.repositories import GossipGenerationRepository, GossipItemRepository
from app.domain.gossip.types import CommonsPhoto, GossipSubject, NearbyContext, WikiPlace
from app.domain.points.repositories import PointRepository
from app.lib.i18n import LocalizedText, LocalizedValue, resolve_text

logger = logging.getLogger(__name__)

ACTIVE_STATUSES: frozenset[GossipStatus] = frozenset({GossipStatus.PENDING, GossipStatus.PROCESSING})
MAX_URL_LENGTH = 2048
MAX_TITLE_LENGTH = 255
MAX_ERROR_LENGTH = 4000


class GossipGenerationService:
    def __init__(
        self,
        session: AsyncSession,
        generations: GossipGenerationRepository,
        items: GossipItemRepository,
        points: PointRepository,
        nearby: NearbySource,
        writer: GossipWriter,
        links: LinkChecker,
        languages: list[str],
        default_language: str,
        radius_m: int,
        max_items: int,
    ) -> None:
        self._session = session
        self._generations = generations
        self._items = items
        self._points = points
        self._nearby = nearby
        self._writer = writer
        self._links = links
        self._languages = languages
        self._default_language = default_language
        self._radius_m = radius_m
        self._max_items = max_items

    async def generate(self, point_id: UUID, attempt_id: UUID) -> None:
        generation = await self._generations.get_one_or_none(point_id=point_id)
        point = await self._points.get_one_or_none(id=point_id)
        if generation is None or point is None or not self._is_current(generation, attempt_id):
            logger.info("Skipping stale gossip task for point %s", point_id)
            return
        generation.status = GossipStatus.PROCESSING
        await self._generations.update(generation, auto_commit=True)
        try:
            items = await self._produce_items(point, generation)
        except Exception as exc:
            logger.exception("Gossip generation failed for point %s", point_id)
            await self._session.rollback()
            await self._finish(generation, attempt_id, GossipStatus.FAILED, error=str(exc), items=None)
            return
        await self._finish(generation, attempt_id, GossipStatus.DONE, error=None, items=items)

    async def _finish(
        self,
        generation: GossipGeneration,
        attempt_id: UUID,
        status: GossipStatus,
        error: str | None,
        items: list[GossipItem] | None,
    ) -> None:
        await self._session.refresh(generation)
        if not self._is_current(generation, attempt_id):
            logger.info("Discarding gossip result for superseded task of point %s", generation.point_id)
            return
        if items is not None:
            await self._items.replace_for_point(generation.point_id, items)
        generation.status = status
        generation.error = error[:MAX_ERROR_LENGTH] if error else None
        generation.finished_at = datetime.now(UTC)
        await self._generations.update(generation, auto_commit=True)

    async def _produce_items(self, point: Point, generation: GossipGeneration) -> list[GossipItem]:
        context = await self._nearby.collect(
            generation.latitude, generation.longitude, self._radius_m, self._max_items
        )
        subject = GossipSubject(
            title=resolve_text(point.title, self._default_language, self._default_language) or "",
            location_name=resolve_text(point.address, self._default_language, self._default_language),
            latitude=generation.latitude,
            longitude=generation.longitude,
        )
        response = await self._writer.write(subject, context, self._max_items, self._languages)
        return await self._build_items(point.id, context, response)

    async def _build_items(
        self, point_id: UUID, context: NearbyContext, response: LlmGossipResponse
    ) -> list[GossipItem]:
        llm_items = [item for item in response.items if self._default_language in item.localizations]
        llm_items = llm_items[: self._max_items]
        extra_urls = [
            link.url for item in llm_items for link in item.extra_links if len(link.url) <= MAX_URL_LENGTH
        ]
        alive_urls = await self._links.filter_alive(extra_urls)
        places = {place.ref: place for place in context.places}
        photos = {photo.ref: photo for photo in context.photos}
        return [
            self._build_item(point_id, position, item, places, photos, alive_urls)
            for position, item in enumerate(llm_items)
        ]

    def _build_item(
        self,
        point_id: UUID,
        position: int,
        item: LlmGossipItem,
        places: dict[str, WikiPlace],
        photos: dict[str, CommonsPhoto],
        alive_urls: set[str],
    ) -> GossipItem:
        place = places.get(item.place_ref) if item.place_ref else None
        photo = photos.get(item.photo_ref) if item.photo_ref else None
        wiki_refs = [ref for ref in item.source_refs if ref in places]
        if place is not None:
            wiki_refs.append(place.ref)
        wiki_sources = [places[ref] for ref in dict.fromkeys(wiki_refs)]
        veracity = item.veracity
        if veracity is GossipVeracity.DOCUMENTED and not wiki_sources:
            veracity = GossipVeracity.UNVERIFIED
        sources = [
            GossipSource(url=source.url, title=source.title[:512], origin=GossipSourceOrigin.WIKIPEDIA)
            for source in wiki_sources
        ]
        known_urls = {source.url for source in sources}
        for link in item.extra_links:
            if link.url in alive_urls and link.url not in known_urls:
                known_urls.add(link.url)
                sources.append(
                    GossipSource(
                        url=link.url,
                        title=link.title[:512] if link.title else None,
                        origin=GossipSourceOrigin.LLM_WEB,
                    )
                )
        anchor = place or photo
        place_name = item.place_name or (place.title if place else None)
        return GossipItem(
            point_id=point_id,
            position=position,
            category=item.category,
            veracity=veracity,
            title=self._localized(item, lambda text: text.title[:MAX_TITLE_LENGTH]),
            text=self._localized(item, lambda text: text.text),
            place_name=place_name[:255] if place_name else None,
            latitude=anchor.latitude if anchor else None,
            longitude=anchor.longitude if anchor else None,
            distance_m=anchor.distance_m if anchor else None,
            photo_url=photo.url if photo else None,
            photo_author=photo.author if photo else None,
            photo_license=photo.license if photo else None,
            photo_source_url=photo.source_url if photo else None,
            is_hidden=False,
            sources=sources,
        )

    def _localized(self, item: LlmGossipItem, pick: Callable[[LlmText], str]) -> LocalizedText:
        return {
            language: LocalizedValue(text=pick(item.localizations[language]))
            for language in self._languages
            if language in item.localizations
        }

    @staticmethod
    def _is_current(generation: GossipGeneration, attempt_id: UUID) -> bool:
        return generation.attempt_id == attempt_id and generation.status in ACTIVE_STATUSES
