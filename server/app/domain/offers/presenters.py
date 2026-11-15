from collections.abc import Sequence
from uuid import UUID

from app.db.models import Offer, Partner
from app.domain.i18n.schemas import localized_out
from app.domain.offers.schemas import AdminOfferOut, MyOfferOut, RedemptionOut
from app.domain.offers.services import GrantView
from app.lib.i18n import resolve_text


def admin_offer_out(offer: Offer) -> AdminOfferOut:
    return AdminOfferOut(
        id=offer.id,
        partner_id=offer.partner_id,
        point_id=offer.point_id,
        title=localized_out(offer.title),
        terms=localized_out(offer.terms),
        promo_code=offer.promo_code,
        valid_until=offer.valid_until,
        ttl_hours=offer.ttl_hours,
        redemption_limit=offer.redemption_limit,
        redemptions_count=offer.redemptions_count,
        is_active=offer.is_active,
    )


class OfferPresenter:
    def __init__(self, language: str, fallback: str) -> None:
        self._language = language
        self._fallback = fallback

    def title(self, offer: Offer) -> str:
        return resolve_text(offer.title, self._language, self._fallback) or ""

    def my_offers(self, views: Sequence[GrantView], partners: dict[UUID, Partner]) -> list[MyOfferOut]:
        return [
            MyOfferOut(
                grant_id=view.grant.id,
                offer_id=view.offer.id,
                partner_name=partners[view.offer.partner_id].name
                if view.offer.partner_id in partners
                else "",
                point_id=view.offer.point_id,
                title=self.title(view.offer),
                terms=resolve_text(view.offer.terms, self._language, self._fallback),
                promo_code=view.offer.promo_code,
                status=view.status,
                granted_at=view.grant.created_at,
                expires_at=view.grant.expires_at,
                redeemed_at=view.grant.redeemed_at,
            )
            for view in views
        ]

    def redemption(self, view: GrantView) -> RedemptionOut:
        return RedemptionOut(
            grant_id=view.grant.id,
            offer_id=view.offer.id,
            offer_title=self.title(view.offer),
            status=view.status,
            granted_at=view.grant.created_at,
            redeemed_at=view.grant.redeemed_at,
        )
