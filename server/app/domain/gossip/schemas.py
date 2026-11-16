from datetime import datetime
from uuid import UUID

from app.db.models import GossipCategory, GossipSourceOrigin, GossipStatus, GossipVeracity
from app.lib.schema import CamelizedBaseStruct


class GossipPhotoOut(CamelizedBaseStruct):
    url: str
    author: str | None
    license: str | None
    source_url: str | None


class GossipSourceOut(CamelizedBaseStruct):
    url: str
    title: str | None
    origin: GossipSourceOrigin


class GossipItemOut(CamelizedBaseStruct):
    id: UUID
    title: str
    text: str
    category: GossipCategory
    veracity: GossipVeracity
    place_name: str | None
    distance_m: int | None
    photo: GossipPhotoOut | None
    sources: list[GossipSourceOut]


class GossipFeedOut(CamelizedBaseStruct):
    status: GossipStatus
    items: list[GossipItemOut]


class GossipTextOut(CamelizedBaseStruct):
    title: str
    text: str


class AdminGossipItemOut(GossipItemOut):
    is_hidden: bool
    translations: dict[str, GossipTextOut]


class AdminGossipFeedOut(CamelizedBaseStruct):
    status: GossipStatus
    enabled: bool
    error: str | None
    finished_at: datetime | None
    items: list[AdminGossipItemOut]


class GossipRegenerateOut(CamelizedBaseStruct):
    status: GossipStatus


class GossipHiddenInput(CamelizedBaseStruct):
    is_hidden: bool
