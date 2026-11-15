from uuid import UUID

from litestar import Controller, delete, get, post, put
from litestar.di import NamedDependency, Provide
from litestar.params import FromPath, FromQuery, JSONBody
from litestar.status_codes import HTTP_200_OK

from app.domain.achievements.deps import provide_achievement_service
from app.domain.achievements.services import AchievementService, Redeemed
from app.domain.auth.guards import requires_admin, requires_registered
from app.domain.offers.controllers import provide_offer_presenter
from app.domain.offers.deps import (
    provide_offer_admin_service,
    provide_offer_service,
    provide_partner_admin_service,
    provide_partner_repository,
)
from app.domain.offers.presenters import OfferPresenter, admin_offer_out
from app.domain.offers.schemas import AdminOfferOut, OfferInput, RedemptionInput, RedemptionOut
from app.domain.offers.services import OfferService
from app.domain.partners.guards import requires_partner_member
from app.domain.partners.schemas import (
    MemberInput,
    MemberOut,
    OfferStatsOut,
    PartnerCabinetOut,
    PartnerInput,
    PartnerOut,
)
from app.domain.partners.services import OfferAdminService, PartnerAdminService, PartnerRepository
from app.lib.request import AppRequest, require_user


class AdminPartnerController(Controller):
    path = "/api/admin/partners"
    tags = ["Admin: Partners"]
    guards = [requires_admin]
    dependencies = {"partner_admin_service": Provide(provide_partner_admin_service)}

    @get("/", summary="List partners", description="All partners.")
    async def list_partners(
        self, partner_admin_service: NamedDependency[PartnerAdminService]
    ) -> list[PartnerOut]:
        return [PartnerOut.from_model(partner) for partner in await partner_admin_service.list_all()]

    @post("/", summary="Create partner", description="Create a partner organisation.")
    async def create_partner(
        self, data: JSONBody[PartnerInput], partner_admin_service: NamedDependency[PartnerAdminService]
    ) -> PartnerOut:
        return PartnerOut.from_model(await partner_admin_service.create(data))

    @put("/{partner_id:uuid}", summary="Update partner", description="Update partner details.")
    async def update_partner(
        self,
        partner_id: FromPath[UUID],
        data: JSONBody[PartnerInput],
        partner_admin_service: NamedDependency[PartnerAdminService],
    ) -> PartnerOut:
        return PartnerOut.from_model(await partner_admin_service.update(partner_id, data))

    @get("/{partner_id:uuid}/members", summary="List staff", description="Accounts that can redeem offers.")
    async def list_members(
        self, partner_id: FromPath[UUID], partner_admin_service: NamedDependency[PartnerAdminService]
    ) -> list[MemberOut]:
        return [MemberOut.from_model(user) for user in await partner_admin_service.members(partner_id)]

    @post(
        "/{partner_id:uuid}/members",
        summary="Add staff",
        description="Grant cabinet access to a registered account.",
    )
    async def add_member(
        self,
        partner_id: FromPath[UUID],
        data: JSONBody[MemberInput],
        partner_admin_service: NamedDependency[PartnerAdminService],
    ) -> MemberOut:
        return MemberOut.from_model(await partner_admin_service.add_member(partner_id, data.email))

    @delete(
        "/{partner_id:uuid}/members/{user_id:uuid}",
        summary="Remove staff",
        description="Revoke cabinet access.",
    )
    async def remove_member(
        self,
        partner_id: FromPath[UUID],
        user_id: FromPath[UUID],
        partner_admin_service: NamedDependency[PartnerAdminService],
    ) -> None:
        await partner_admin_service.remove_member(partner_id, user_id)


class AdminOfferController(Controller):
    path = "/api/admin/offers"
    tags = ["Admin: Partners"]
    guards = [requires_admin]
    dependencies = {"offer_admin_service": Provide(provide_offer_admin_service)}

    @get("/", summary="List offers", description="Offers, optionally filtered by partner.")
    async def list_offers(
        self,
        offer_admin_service: NamedDependency[OfferAdminService],
        partner_id: FromQuery[UUID | None] = None,
    ) -> list[AdminOfferOut]:
        return [admin_offer_out(offer) for offer in await offer_admin_service.list_all(partner_id)]

    @post(
        "/",
        summary="Create offer",
        description="Create a promo code or note offer, optionally bound to a point.",
    )
    async def create_offer(
        self, data: JSONBody[OfferInput], offer_admin_service: NamedDependency[OfferAdminService]
    ) -> AdminOfferOut:
        return admin_offer_out(await offer_admin_service.create(data))

    @get("/{offer_id:uuid}", summary="Get offer", description="Offer with all translations.")
    async def get_offer(
        self, offer_id: FromPath[UUID], offer_admin_service: NamedDependency[OfferAdminService]
    ) -> AdminOfferOut:
        return admin_offer_out(await offer_admin_service.get(offer_id))

    @put("/{offer_id:uuid}", summary="Update offer", description="Update offer settings.")
    async def update_offer(
        self,
        offer_id: FromPath[UUID],
        data: JSONBody[OfferInput],
        offer_admin_service: NamedDependency[OfferAdminService],
    ) -> AdminOfferOut:
        return admin_offer_out(await offer_admin_service.update(offer_id, data))

    @delete("/{offer_id:uuid}", summary="Delete offer", description="Delete an offer without redemptions.")
    async def delete_offer(
        self, offer_id: FromPath[UUID], offer_admin_service: NamedDependency[OfferAdminService]
    ) -> None:
        await offer_admin_service.delete(offer_id)


class PartnerCabinetController(Controller):
    path = "/api/partner"
    tags = ["Partner cabinet"]
    dependencies = {
        "partner_repository": Provide(provide_partner_repository),
        "offer_service": Provide(provide_offer_service),
        "offer_presenter": Provide(provide_offer_presenter),
        "offer_admin_service": Provide(provide_offer_admin_service),
        "achievement_service": Provide(provide_achievement_service),
    }

    @get(
        "/",
        summary="My partners",
        description="Partners the current account can act for.",
        guards=[requires_registered],
    )
    async def my_partners(
        self, request: AppRequest, partner_repository: NamedDependency[PartnerRepository]
    ) -> list[PartnerCabinetOut]:
        partners = await partner_repository.for_member(require_user(request).id)
        return [PartnerCabinetOut(id=partner.id, name=partner.name) for partner in partners]

    @post(
        "/{partner_id:uuid}/redemptions/lookup",
        summary="Check offer",
        description="Show what a scanned QR or entered code grants without redeeming it.",
        guards=[requires_partner_member],
        status_code=HTTP_200_OK,
    )
    async def lookup(
        self,
        partner_id: FromPath[UUID],
        data: JSONBody[RedemptionInput],
        offer_service: NamedDependency[OfferService],
        offer_presenter: NamedDependency[OfferPresenter],
    ) -> RedemptionOut:
        return offer_presenter.redemption(await offer_service.lookup(partner_id, data.token, data.code))

    @post(
        "/{partner_id:uuid}/redemptions",
        summary="Redeem offer",
        description="Confirm that the guest received the offer; enforces expiry and redemption limits.",
        guards=[requires_partner_member],
        status_code=HTTP_200_OK,
    )
    async def redeem(
        self,
        request: AppRequest,
        partner_id: FromPath[UUID],
        data: JSONBody[RedemptionInput],
        offer_service: NamedDependency[OfferService],
        offer_presenter: NamedDependency[OfferPresenter],
        achievement_service: NamedDependency[AchievementService],
    ) -> RedemptionOut:
        view = await offer_service.redeem(partner_id, require_user(request).id, data.token, data.code)
        if view.grant.redeemed_at is not None:
            await achievement_service.evaluate(
                Redeemed(user_id=view.grant.user_id, at=view.grant.redeemed_at)
            )
        return offer_presenter.redemption(view)

    @get(
        "/{partner_id:uuid}/redemptions",
        summary="Recent redemptions",
        description="Latest confirmed redemptions of this partner's offers.",
        guards=[requires_partner_member],
    )
    async def recent(
        self,
        partner_id: FromPath[UUID],
        offer_service: NamedDependency[OfferService],
        offer_presenter: NamedDependency[OfferPresenter],
        offer_admin_service: NamedDependency[OfferAdminService],
    ) -> list[RedemptionOut]:
        offers = await offer_admin_service.list_all(partner_id)
        return [offer_presenter.redemption(view) for view in await offer_service.recent_redemptions(offers)]

    @get(
        "/{partner_id:uuid}/stats",
        summary="Offer statistics",
        description="Granted and redeemed counts per offer.",
        guards=[requires_partner_member],
    )
    async def stats(
        self,
        partner_id: FromPath[UUID],
        offer_service: NamedDependency[OfferService],
        offer_presenter: NamedDependency[OfferPresenter],
        offer_admin_service: NamedDependency[OfferAdminService],
    ) -> list[OfferStatsOut]:
        offers = await offer_admin_service.list_all(partner_id)
        stats = await offer_service.partner_stats([offer.id for offer in offers])
        return [
            OfferStatsOut(
                offer_id=offer.id,
                title=offer_presenter.title(offer),
                point_id=offer.point_id,
                granted=stats[offer.id].granted if offer.id in stats else 0,
                redeemed=stats[offer.id].redeemed if offer.id in stats else 0,
                redemption_limit=offer.redemption_limit,
                is_active=offer.is_active,
            )
            for offer in offers
        ]
