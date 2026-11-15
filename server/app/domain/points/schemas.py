from datetime import datetime
from typing import Annotated
from uuid import UUID

import msgspec

from app.db.models import BlockKind, PointKind
from app.domain.i18n.schemas import LocalizedField, LocalizedInput
from app.lib.schema import CamelizedBaseStruct

Latitude = Annotated[float, msgspec.Meta(ge=-90, le=90)]
Longitude = Annotated[float, msgspec.Meta(ge=-180, le=180)]


class BlockInput(CamelizedBaseStruct):
    kind: BlockKind
    text: LocalizedInput | None = None
    caption: LocalizedInput | None = None
    transcript: LocalizedInput | None = None
    asset_id: UUID | None = None
    media_variants: dict[str, UUID] = msgspec.field(default_factory=dict)


class PointInput(CamelizedBaseStruct):
    kind: PointKind
    title: LocalizedInput
    latitude: Latitude
    longitude: Longitude
    address: LocalizedInput | None = None
    note: LocalizedInput | None = None
    cover_asset_id: UUID | None = None
    partner_id: UUID | None = None
    is_published: bool = False
    blocks: Annotated[list[BlockInput], msgspec.Meta(max_length=50)] = msgspec.field(default_factory=list)


class AdminBlockOut(CamelizedBaseStruct):
    id: UUID
    kind: BlockKind
    text: dict[str, LocalizedField]
    caption: dict[str, LocalizedField]
    transcript: dict[str, LocalizedField]
    asset_id: UUID | None
    media_variants: dict[str, UUID]


class AdminPointOut(CamelizedBaseStruct):
    id: UUID
    kind: PointKind
    title: dict[str, LocalizedField]
    latitude: float
    longitude: float
    address: dict[str, LocalizedField]
    note: dict[str, LocalizedField]
    cover_asset_id: UUID | None
    partner_id: UUID | None
    is_published: bool
    blocks: list[AdminBlockOut]
    created_at: datetime
    updated_at: datetime


class AdminPointSummary(CamelizedBaseStruct):
    id: UUID
    kind: PointKind
    title: dict[str, LocalizedField]
    latitude: float
    longitude: float
    is_published: bool
    updated_at: datetime


class BlockOut(CamelizedBaseStruct):
    kind: BlockKind
    text: str | None
    caption: str | None
    transcript: str | None
    asset_id: UUID | None
    media_url: str | None
    content_type: str | None


class PointCard(CamelizedBaseStruct):
    id: UUID
    kind: PointKind
    title: str
    cover_url: str | None


class PointContentOut(CamelizedBaseStruct):
    id: UUID
    kind: PointKind
    title: str
    address: str | None
    note: str | None
    latitude: float
    longitude: float
    cover_url: str | None
    blocks: list[BlockOut]
    unlocked_at: datetime


class CollectionItem(CamelizedBaseStruct):
    point: PointCard
    unlocked_at: datetime
