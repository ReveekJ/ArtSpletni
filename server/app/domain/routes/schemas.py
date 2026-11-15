from datetime import datetime
from typing import Annotated
from uuid import UUID

import msgspec

from app.db.models import MapVisibility, OrderingMode, PointKind
from app.domain.i18n.schemas import LocalizedField, LocalizedInput
from app.domain.routes.progress import IssueCode
from app.lib.schema import CamelizedBaseStruct

Slug = Annotated[str, msgspec.Meta(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=80)]


class RouteInput(CamelizedBaseStruct):
    slug: Slug
    title: LocalizedInput
    description: LocalizedInput | None = None
    cover_asset_id: UUID | None = None
    ordering_mode: OrderingMode = OrderingMode.FREE
    map_visibility: MapVisibility = MapVisibility.ALL
    active_from: datetime | None = None
    active_until: datetime | None = None
    is_repeatable: bool = False


class StopInput(CamelizedBaseStruct):
    point_id: UUID
    is_start: bool = False
    is_required: bool = True
    hint: LocalizedInput | None = None


class StopUpdate(CamelizedBaseStruct):
    is_start: bool | None = None
    is_required: bool | None = None
    hint: LocalizedInput | None = None
    graph_x: float | None = None
    graph_y: float | None = None


class StopOrderInput(CamelizedBaseStruct):
    stop_ids: list[UUID]


class DependencyInput(CamelizedBaseStruct):
    depends_on_stop_id: UUID


class IssueOut(CamelizedBaseStruct):
    code: IssueCode
    stop_id: UUID | None


class StopPointOut(CamelizedBaseStruct):
    id: UUID
    kind: PointKind
    title: dict[str, LocalizedField]
    latitude: float
    longitude: float
    is_published: bool


class AdminStopOut(CamelizedBaseStruct):
    id: UUID
    point: StopPointOut
    position: int
    is_start: bool
    is_required: bool
    hint: dict[str, LocalizedField]
    graph_x: float | None
    graph_y: float | None
    depends_on: list[UUID]


class AdminRouteSummary(CamelizedBaseStruct):
    id: UUID
    slug: str
    title: dict[str, LocalizedField]
    ordering_mode: OrderingMode
    is_published: bool
    stop_count: int
    updated_at: datetime


class AdminRouteOut(CamelizedBaseStruct):
    id: UUID
    slug: str
    title: dict[str, LocalizedField]
    description: dict[str, LocalizedField]
    cover_asset_id: UUID | None
    ordering_mode: OrderingMode
    map_visibility: MapVisibility
    active_from: datetime | None
    active_until: datetime | None
    is_repeatable: bool
    is_published: bool
    stops: list[AdminStopOut]
    issues: list[IssueOut]
