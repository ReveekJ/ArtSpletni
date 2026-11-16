from datetime import timedelta

from litestar.di import NamedDependency
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.gossip.generation import GossipGenerationService
from app.domain.gossip.links import LinkValidator
from app.domain.gossip.llm import MAX_ATTEMPTS, GossipWriterError, LlmGossipWriter
from app.domain.gossip.llm_schema import LlmGossipResponse
from app.domain.gossip.protocols import GossipWriter, LinkChecker, NearbySource
from app.domain.gossip.repositories import GossipGenerationRepository, GossipItemRepository
from app.domain.gossip.service import GossipService
from app.domain.gossip.types import GossipSubject, NearbyContext
from app.domain.gossip.wiki import WikiGeoClient
from app.domain.points.repositories import PointRepository, UnlockRepository
from app.lib.settings import get_settings

STALE_GRACE_SECONDS = 120


class DisabledGossipWriter:
    async def write(
        self, subject: GossipSubject, context: NearbyContext, max_items: int, languages: list[str]
    ) -> LlmGossipResponse:
        raise GossipWriterError("LLM is not configured (set LLM__BASE_URL and LLM__MODEL)")


def gossip_writer() -> GossipWriter:
    llm = get_settings().llm
    if llm is None:
        return DisabledGossipWriter()
    return LlmGossipWriter(llm)


def nearby_source() -> NearbySource:
    gossip = get_settings().gossip
    return WikiGeoClient(gossip.http_user_agent, gossip.http_timeout_seconds)


def link_checker() -> LinkChecker:
    gossip = get_settings().gossip
    return LinkValidator(gossip.http_user_agent, gossip.http_timeout_seconds)


def build_generation_service(session: AsyncSession) -> GossipGenerationService:
    settings = get_settings()
    return GossipGenerationService(
        session=session,
        generations=GossipGenerationRepository(session=session),
        items=GossipItemRepository(session=session),
        points=PointRepository(session=session),
        nearby=nearby_source(),
        writer=gossip_writer(),
        links=link_checker(),
        languages=settings.languages,
        default_language=settings.default_language,
        radius_m=settings.gossip.radius_m,
        max_items=settings.gossip.max_items,
    )


async def provide_gossip_service(
    db_session: NamedDependency[AsyncSession], language: NamedDependency[str]
) -> GossipService:
    settings = get_settings()
    llm_timeout = settings.llm.timeout_seconds if settings.llm else 0.0
    return GossipService(
        generations=GossipGenerationRepository(session=db_session),
        items=GossipItemRepository(session=db_session),
        points=PointRepository(session=db_session),
        unlocks=UnlockRepository(session=db_session),
        language=language,
        fallback_language=settings.default_language,
        enabled=settings.llm is not None,
        stale_after=timedelta(seconds=llm_timeout * MAX_ATTEMPTS + STALE_GRACE_SECONDS),
        failed_retry_after=timedelta(minutes=settings.gossip.failed_retry_minutes),
    )
