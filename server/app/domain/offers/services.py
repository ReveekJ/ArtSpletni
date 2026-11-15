from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from app.db.models import Offer, OfferGrant
from app.domain.offers.repositories import GrantStats, OfferGrantRepository, OfferRepository
from app.domain.offers.tokens import (
    generate_redemption_code,
    issue_qr_token,
    normalize_code,
    verify_qr_token,
)
from app.domain.runs.services import utcnow
from app.lib.exceptions import BadRequestError, ConflictError, NotFoundError


class GrantStatus(StrEnum):
    ACTIVE = "active"
    REDEEMED = "redeemed"
    EXPIRED = "expired"
    EXHAUSTED = "exhausted"


@dataclass(frozen=True, slots=True)
class GrantView:
    grant: OfferGrant
    offer: Offer
    status: GrantStatus


@dataclass(frozen=True, slots=True)
class QrToken:
    token: str
    code: str
    expires_at: datetime


def grant_status(grant: OfferGrant, offer: Offer, now: datetime) -> GrantStatus:
    if grant.redeemed_at is not None:
        return GrantStatus.REDEEMED
    if grant.expires_at is not None and grant.expires_at <= now:
        return GrantStatus.EXPIRED
    if offer.is_exhausted or not offer.is_active:
        return GrantStatus.EXHAUSTED
    return GrantStatus.ACTIVE


class OfferService:
    def __init__(self, offers: OfferRepository, grants: OfferGrantRepository, signing_key: str) -> None:
        self._offers = offers
        self._grants = grants
        self._key = signing_key

    async def offer_for_point(self, point_id: UUID) -> Offer | None:
        return await self._offers.get_one_or_none(point_id=point_id)

    async def grant(self, user_id: UUID, offer: Offer, at: datetime) -> OfferGrant | None:
        if not offer.is_active or offer.is_exhausted:
            return None
        if offer.valid_until is not None and offer.valid_until <= at:
            return None
        expires_at = offer.valid_until
        if offer.ttl_hours is not None:
            ttl_expiry = at + timedelta(hours=offer.ttl_hours)
            expires_at = min(expires_at, ttl_expiry) if expires_at else ttl_expiry
        grant_id = await self._grants.insert_if_absent(
            offer.id, user_id, generate_redemption_code(), expires_at
        )
        if grant_id is None:
            return None
        return await self._grants.get(grant_id)

    async def my_grants(self, user_id: UUID) -> list[GrantView]:
        grants = await self._grants.for_user(user_id)
        offers = await self._offers_by_id({grant.offer_id for grant in grants})
        now = utcnow()
        return [
            GrantView(grant, offers[grant.offer_id], grant_status(grant, offers[grant.offer_id], now))
            for grant in grants
            if grant.offer_id in offers
        ]

    async def qr_token(self, user_id: UUID, grant_id: UUID) -> QrToken:
        grant = await self._grants.get_one_or_none(id=grant_id, user_id=user_id)
        if grant is None:
            raise NotFoundError("Offer not found", code="grant_not_found")
        token, expires_at = issue_qr_token(grant.id, self._key, utcnow())
        return QrToken(token=token, code=grant.redemption_code, expires_at=expires_at)

    async def lookup(self, partner_id: UUID, token: str | None, code: str | None) -> GrantView:
        grant = await self._find_grant(token, code)
        offer = await self._offers.get_one_or_none(id=grant.offer_id) if grant else None
        if grant is None or offer is None or offer.partner_id != partner_id:
            raise NotFoundError("Offer not found for this partner", code="grant_not_found")
        return GrantView(grant, offer, grant_status(grant, offer, utcnow()))

    async def redeem(
        self, partner_id: UUID, staff_id: UUID, token: str | None, code: str | None
    ) -> GrantView:
        view = await self.lookup(partner_id, token, code)
        offer = await self._offers.lock(view.offer.id)
        if offer is None:
            raise NotFoundError("Offer not found", code="grant_not_found")
        now = utcnow()
        status = grant_status(view.grant, offer, now)
        if status is not GrantStatus.ACTIVE:
            raise ConflictError(f"Offer cannot be redeemed: {status}", code=f"grant_{status}")
        view.grant.redeemed_at = now
        view.grant.redeemed_by_id = staff_id
        offer.redemptions_count += 1
        await self._offers.update(offer, auto_refresh=False)
        grant = await self._grants.update(view.grant, auto_refresh=False)
        return GrantView(grant, offer, GrantStatus.REDEEMED)

    async def partner_stats(self, offer_ids: Sequence[UUID]) -> dict[UUID, GrantStats]:
        return await self._grants.stats(offer_ids)

    async def recent_redemptions(self, offers: Sequence[Offer], limit: int = 50) -> list[GrantView]:
        by_id = {offer.id: offer for offer in offers}
        grants = await self._grants.recent_redemptions(list(by_id), limit)
        return [GrantView(grant, by_id[grant.offer_id], GrantStatus.REDEEMED) for grant in grants]

    async def _find_grant(self, token: str | None, code: str | None) -> OfferGrant | None:
        if token:
            grant_id = verify_qr_token(token, self._key, utcnow())
            if grant_id is None:
                raise BadRequestError("QR code is invalid or expired", code="invalid_qr_token")
            return await self._grants.get_one_or_none(id=grant_id)
        if code:
            return await self._grants.get_one_or_none(redemption_code=normalize_code(code))
        raise BadRequestError("Provide a QR token or a code", code="redemption_input_required")

    async def _offers_by_id(self, offer_ids: set[UUID]) -> dict[UUID, Offer]:
        if not offer_ids:
            return {}
        return {offer.id: offer for offer in await self._offers.get_many(Offer.id.in_(offer_ids))}
