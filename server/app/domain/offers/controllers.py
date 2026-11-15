from uuid import UUID

from litestar import Controller, get, post
from litestar.di import NamedDependency, Provide
from litestar.params import FromPath
from litestar.status_codes import HTTP_200_OK

from app.db.models import Partner
from app.domain.auth.guards import requires_actor
from app.domain.offers.deps import provide_offer_service, provide_partner_repository
from app.domain.offers.presenters import OfferPresenter
from app.domain.offers.schemas import MyOfferOut, QrTokenOut
from app.domain.offers.services import OfferService
from app.domain.partners.services import PartnerRepository
from app.lib.request import AppRequest, require_user
from app.lib.settings import get_settings


async def provide_offer_presenter(language: NamedDependency[str]) -> OfferPresenter:
    return OfferPresenter(language, get_settings().default_language)


class MyOffersController(Controller):
    path = "/api/me/offers"
    tags = ["Me"]
    guards = [requires_actor]
    dependencies = {
        "offer_service": Provide(provide_offer_service),
        "offer_presenter": Provide(provide_offer_presenter),
        "partner_repository": Provide(provide_partner_repository),
    }

    @get("/", summary="My offers", description="Promo codes and partner offers granted to the current user.")
    async def my_offers(
        self,
        request: AppRequest,
        offer_service: NamedDependency[OfferService],
        offer_presenter: NamedDependency[OfferPresenter],
        partner_repository: NamedDependency[PartnerRepository],
    ) -> list[MyOfferOut]:
        views = await offer_service.my_grants(require_user(request).id)
        partner_ids = {view.offer.partner_id for view in views}
        partners = (
            {
                partner.id: partner
                for partner in await partner_repository.get_many(Partner.id.in_(partner_ids))
            }
            if partner_ids
            else {}
        )
        return offer_presenter.my_offers(views, partners)

    @post(
        "/{grant_id:uuid}/qr",
        summary="Redemption QR",
        description="Issue a short-lived signed token to show as a QR code to partner staff.",
        status_code=HTTP_200_OK,
    )
    async def qr_token(
        self,
        request: AppRequest,
        grant_id: FromPath[UUID],
        offer_service: NamedDependency[OfferService],
    ) -> QrTokenOut:
        token = await offer_service.qr_token(require_user(request).id, grant_id)
        return QrTokenOut(token=token.token, code=token.code, expires_at=token.expires_at)
