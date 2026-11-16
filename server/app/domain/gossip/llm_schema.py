import msgspec

from app.db.models import GossipCategory, GossipVeracity


class LlmText(msgspec.Struct):
    title: str
    text: str


class LlmLink(msgspec.Struct):
    url: str
    title: str | None = None


class LlmGossipItem(msgspec.Struct):
    category: GossipCategory
    veracity: GossipVeracity
    localizations: dict[str, LlmText]
    place_name: str | None = None
    place_ref: str | None = None
    photo_ref: str | None = None
    source_refs: list[str] = []
    extra_links: list[LlmLink] = []


class LlmGossipResponse(msgspec.Struct):
    items: list[LlmGossipItem]
