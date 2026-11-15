from typing import Annotated
from uuid import UUID

import msgspec

from app.db.models import Partner, User
from app.domain.i18n.schemas import LocalizedField, LocalizedInput, localized_out
from app.lib.schema import CamelizedBaseStruct


class PartnerInput(CamelizedBaseStruct):
    name: Annotated[str, msgspec.Meta(min_length=1, max_length=160)]
    description: LocalizedInput | None = None
    logo_asset_id: UUID | None = None
    is_active: bool = True


class PartnerOut(CamelizedBaseStruct):
    id: UUID
    name: str
    description: dict[str, LocalizedField]
    logo_asset_id: UUID | None
    is_active: bool

    @classmethod
    def from_model(cls, partner: Partner) -> "PartnerOut":
        return cls(
            id=partner.id,
            name=partner.name,
            description=localized_out(partner.description),
            logo_asset_id=partner.logo_asset_id,
            is_active=partner.is_active,
        )


class MemberInput(CamelizedBaseStruct):
    email: Annotated[str, msgspec.Meta(max_length=320)]


class MemberOut(CamelizedBaseStruct):
    user_id: UUID
    email: str | None
    display_name: str | None

    @classmethod
    def from_model(cls, user: User) -> "MemberOut":
        return cls(user_id=user.id, email=user.email, display_name=user.display_name)


class OfferStatsOut(CamelizedBaseStruct):
    offer_id: UUID
    title: str
    point_id: UUID | None
    granted: int
    redeemed: int
    redemption_limit: int | None
    is_active: bool


class PartnerCabinetOut(CamelizedBaseStruct):
    id: UUID
    name: str
