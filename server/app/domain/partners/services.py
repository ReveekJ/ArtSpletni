from collections.abc import Sequence
from uuid import UUID

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select

from app.db.models import MediaKind, Offer, Partner, PartnerMember, Point, PointKind, User
from app.domain.i18n.services import TranslationService
from app.domain.media.services import MediaService
from app.domain.offers.repositories import OfferRepository
from app.domain.offers.schemas import OfferInput
from app.domain.partners.schemas import PartnerInput
from app.domain.points.repositories import PointRepository
from app.domain.users.services import UserService
from app.lib.exceptions import BadRequestError, ConflictError, NotFoundError


class PartnerRepository(SQLAlchemyAsyncRepository[Partner]):
    model_type = Partner

    async def for_member(self, user_id: UUID) -> Sequence[Partner]:
        members = select(PartnerMember.partner_id).where(PartnerMember.user_id == user_id)
        return await self.get_many(Partner.id.in_(members), Partner.is_active.is_(True))


class PartnerMemberRepository(SQLAlchemyAsyncRepository[PartnerMember]):
    model_type = PartnerMember


class PartnerAdminService:
    def __init__(
        self,
        partners: PartnerRepository,
        members: PartnerMemberRepository,
        users: UserService,
        media: MediaService,
        translator: TranslationService,
    ) -> None:
        self._partners = partners
        self._members = members
        self._users = users
        self._media = media
        self._translator = translator

    async def list_all(self) -> Sequence[Partner]:
        return await self._partners.get_many(order_by=[(Partner.name, False)])

    async def get(self, partner_id: UUID) -> Partner:
        partner = await self._partners.get_one_or_none(id=partner_id)
        if partner is None:
            raise NotFoundError("Partner not found", code="partner_not_found")
        return partner

    async def create(self, data: PartnerInput) -> Partner:
        partner = Partner(name=data.name)
        await self._apply(partner, data)
        return await self._partners.add(partner)

    async def update(self, partner_id: UUID, data: PartnerInput) -> Partner:
        partner = await self.get(partner_id)
        await self._apply(partner, data)
        return await self._partners.update(partner, auto_refresh=False)

    async def members(self, partner_id: UUID) -> Sequence[User]:
        await self.get(partner_id)
        member_ids = select(PartnerMember.user_id).where(PartnerMember.partner_id == partner_id)
        return await self._users.get_many(User.id.in_(member_ids))

    async def add_member(self, partner_id: UUID, email: str) -> User:
        await self.get(partner_id)
        user = await self._users.get_by_email(email)
        if user is None or user.is_guest:
            raise NotFoundError("No registered account with this email", code="user_not_found")
        if await self._members.get_one_or_none(partner_id=partner_id, user_id=user.id) is None:
            await self._members.add(PartnerMember(partner_id=partner_id, user_id=user.id))
        return user

    async def remove_member(self, partner_id: UUID, user_id: UUID) -> None:
        member = await self._members.get_one_or_none(partner_id=partner_id, user_id=user_id)
        if member is not None:
            await self._members.delete(member.id)

    async def _apply(self, partner: Partner, data: PartnerInput) -> None:
        partner.name = data.name
        partner.description = (
            await self._translator.localize(data.description, partner.description, required=False)
            if data.description is not None
            else None
        )
        if data.logo_asset_id is not None:
            await self._media.get_ready(data.logo_asset_id, MediaKind.IMAGE)
        partner.logo_asset_id = data.logo_asset_id
        partner.is_active = data.is_active


class OfferAdminService:
    def __init__(
        self,
        offers: OfferRepository,
        partners: PartnerRepository,
        points: PointRepository,
        translator: TranslationService,
    ) -> None:
        self._offers = offers
        self._partners = partners
        self._points = points
        self._translator = translator

    async def list_all(self, partner_id: UUID | None) -> Sequence[Offer]:
        filters = [Offer.partner_id == partner_id] if partner_id else []
        return await self._offers.get_many(*filters, order_by=[(Offer.created_at, True)])

    async def get(self, offer_id: UUID) -> Offer:
        offer = await self._offers.get_one_or_none(id=offer_id)
        if offer is None:
            raise NotFoundError("Offer not found", code="offer_not_found")
        return offer

    async def create(self, data: OfferInput) -> Offer:
        offer = Offer(partner_id=data.partner_id, title={})
        await self._apply(offer, data)
        return await self._offers.add(offer)

    async def update(self, offer_id: UUID, data: OfferInput) -> Offer:
        offer = await self.get(offer_id)
        await self._apply(offer, data)
        return await self._offers.update(offer, auto_refresh=False)

    async def delete(self, offer_id: UUID) -> None:
        offer = await self.get(offer_id)
        if offer.redemptions_count:
            raise ConflictError("Offer has redemptions; deactivate it instead", code="offer_has_redemptions")
        await self._offers.delete(offer.id)

    async def _apply(self, offer: Offer, data: OfferInput) -> None:
        if await self._partners.get_one_or_none(id=data.partner_id) is None:
            raise NotFoundError("Partner not found", code="partner_not_found")
        if data.point_id is not None:
            await self._check_point(data.point_id, data.partner_id, offer.id)
        title = await self._translator.localize(data.title, offer.title or None)
        if title is None:
            raise BadRequestError("Title is required", code="title_required")
        offer.partner_id = data.partner_id
        offer.point_id = data.point_id
        offer.title = title
        offer.terms = (
            await self._translator.localize(data.terms, offer.terms, required=False)
            if data.terms is not None
            else None
        )
        offer.promo_code = data.promo_code.strip() if data.promo_code else None
        offer.valid_until = data.valid_until
        offer.ttl_hours = data.ttl_hours
        offer.redemption_limit = data.redemption_limit
        offer.is_active = data.is_active

    async def _check_point(self, point_id: UUID, partner_id: UUID, offer_id: UUID | None) -> None:
        point: Point | None = await self._points.get_one_or_none(id=point_id)
        if point is None:
            raise NotFoundError("Point not found", code="point_not_found")
        if point.kind is not PointKind.PARTNER or point.partner_id != partner_id:
            raise BadRequestError(
                "Offer point must be a partner point of the same partner", code="offer_point_mismatch"
            )
        existing = await self._offers.get_one_or_none(point_id=point_id)
        if existing is not None and existing.id != offer_id:
            raise ConflictError("Point already has an offer", code="point_has_offer")
