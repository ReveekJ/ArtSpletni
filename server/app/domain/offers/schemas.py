from datetime import datetime
from typing import Annotated
from uuid import UUID

import msgspec

from app.domain.i18n.schemas import LocalizedField, LocalizedInput
from app.domain.offers.services import GrantStatus
from app.lib.schema import CamelizedBaseStruct


class OfferInput(CamelizedBaseStruct):
    partner_id: UUID
    title: LocalizedInput
    point_id: UUID | None = None
    terms: LocalizedInput | None = None
    promo_code: Annotated[str, msgspec.Meta(min_length=1, max_length=64)] | None = None
    valid_until: datetime | None = None
    ttl_hours: Annotated[int, msgspec.Meta(gt=0, le=24 * 365)] | None = None
    redemption_limit: Annotated[int, msgspec.Meta(gt=0)] | None = None
    is_active: bool = True


class AdminOfferOut(CamelizedBaseStruct):
    id: UUID
    partner_id: UUID
    point_id: UUID | None
    title: dict[str, LocalizedField]
    terms: dict[str, LocalizedField]
    promo_code: str | None
    valid_until: datetime | None
    ttl_hours: int | None
    redemption_limit: int | None
    redemptions_count: int
    is_active: bool


class MyOfferOut(CamelizedBaseStruct):
    grant_id: UUID
    offer_id: UUID
    partner_name: str
    point_id: UUID | None
    title: str
    terms: str | None
    promo_code: str | None
    status: GrantStatus
    granted_at: datetime
    expires_at: datetime | None
    redeemed_at: datetime | None


class QrTokenOut(CamelizedBaseStruct):
    token: str
    code: str
    expires_at: datetime


class RedemptionInput(CamelizedBaseStruct):
    token: Annotated[str, msgspec.Meta(max_length=200)] | None = None
    code: Annotated[str, msgspec.Meta(max_length=32)] | None = None


class RedemptionOut(CamelizedBaseStruct):
    grant_id: UUID
    offer_id: UUID
    offer_title: str
    status: GrantStatus
    granted_at: datetime
    redeemed_at: datetime | None
