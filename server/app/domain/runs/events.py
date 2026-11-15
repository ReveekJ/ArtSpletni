from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from app.lib.schema import CamelizedBaseStruct


@dataclass(frozen=True, slots=True)
class PointUnlocked:
    user_id: UUID
    point_id: UUID
    at: datetime


@dataclass(frozen=True, slots=True)
class StopVisited:
    user_id: UUID
    run_id: UUID
    route_id: UUID
    stop_id: UUID
    point_id: UUID
    at: datetime


@dataclass(frozen=True, slots=True)
class RouteCompleted:
    user_id: UUID
    run_id: UUID
    route_id: UUID
    started_at: datetime
    at: datetime
    fully: bool


ProgressEvent = PointUnlocked | StopVisited | RouteCompleted


class Notification(CamelizedBaseStruct):
    kind: str
    id: UUID
    title: str | None = None


@runtime_checkable
class ProgressListener(Protocol):
    async def handle(self, event: ProgressEvent) -> Sequence[Notification]: ...


class ProgressEventBus:
    def __init__(self, listeners: Sequence[ProgressListener]) -> None:
        self._listeners = listeners

    async def publish(self, events: Sequence[ProgressEvent]) -> list[Notification]:
        notifications: list[Notification] = []
        for event in events:
            for listener in self._listeners:
                notifications.extend(await listener.handle(event))
        return notifications
