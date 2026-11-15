from typing import Annotated
from uuid import UUID

import msgspec

from app.lib.schema import CamelizedBaseStruct

Seconds = Annotated[float, msgspec.Meta(ge=0, le=6 * 3600)]


class PlaybackInput(CamelizedBaseStruct):
    point_id: UUID
    asset_id: UUID
    session_key: Annotated[str, msgspec.Meta(min_length=8, max_length=64)]
    position_seconds: Seconds
    duration_seconds: Seconds


class OverviewOut(CamelizedBaseStruct):
    days: int
    scans: int
    failed_scans: int
    active_users: int
    new_accounts: int
    runs_started: int
    runs_completed: int
    offers_granted: int
    offers_redeemed: int


class PointActivityOut(CamelizedBaseStruct):
    point_id: UUID
    title: str
    scans: int
    unique_users: int


class FunnelStopOut(CamelizedBaseStruct):
    stop_id: UUID
    position: int
    title: str
    visits: int


class RouteFunnelOut(CamelizedBaseStruct):
    route_id: UUID
    started: int
    completed: int
    stops: list[FunnelStopOut]


class PlaybackActivityOut(CamelizedBaseStruct):
    point_id: UUID
    asset_id: UUID
    sessions: int
    completed: int
    average_ratio: float
