from typing import Protocol

from app.domain.gossip.llm_schema import LlmGossipResponse
from app.domain.gossip.types import GossipSubject, NearbyContext


class NearbySource(Protocol):
    async def collect(
        self, latitude: float, longitude: float, radius_m: int, limit: int
    ) -> NearbyContext: ...


class GossipWriter(Protocol):
    async def write(
        self, subject: GossipSubject, context: NearbyContext, max_items: int, languages: list[str]
    ) -> LlmGossipResponse: ...


class LinkChecker(Protocol):
    async def filter_alive(self, urls: list[str]) -> set[str]: ...
