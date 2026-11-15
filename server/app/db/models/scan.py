from enum import StrEnum
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.types import str_enum


class ScanOutcome(StrEnum):
    INVALID_TAG = "invalid_tag"
    POINT_UNAVAILABLE = "point_unavailable"
    UNLOCKED = "unlocked"
    VISITED = "visited"
    REVISITED = "revisited"
    ROUTE_STARTED = "route_started"
    ROUTE_COMPLETED = "route_completed"
    LOCKED = "locked"
    CHOOSE_ROUTE = "choose_route"
    SWITCH_OFFER = "switch_offer"
    NOT_A_START = "not_a_start"


class ScanEvent(UUIDv7AuditBase):
    __tablename__ = "scan_events"

    outcome: Mapped[ScanOutcome] = mapped_column(str_enum(ScanOutcome), index=True)
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None, index=True
    )
    tag_id: Mapped[UUID | None] = mapped_column(ForeignKey("nfc_tags.id", ondelete="SET NULL"), default=None)
    point_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("points.id", ondelete="SET NULL"), default=None, index=True
    )
    route_id: Mapped[UUID | None] = mapped_column(ForeignKey("routes.id", ondelete="SET NULL"), default=None)
