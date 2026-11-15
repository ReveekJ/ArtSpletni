from litestar.di import NamedDependency
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.i18n.services import TranslationService
from app.domain.media.services import MediaService
from app.domain.offers.repositories import OfferGrantRepository, OfferRepository
from app.domain.offers.services import OfferService
from app.domain.partners.services import (
    OfferAdminService,
    PartnerAdminService,
    PartnerMemberRepository,
    PartnerRepository,
)
from app.domain.points.repositories import PointRepository
from app.domain.users.services import UserService
from app.lib.settings import get_settings


def build_offer_service(db_session: AsyncSession) -> OfferService:
    return OfferService(
        OfferRepository(session=db_session),
        OfferGrantRepository(session=db_session),
        get_settings().secret_key.get_secret_value(),
    )


async def provide_offer_service(db_session: NamedDependency[AsyncSession]) -> OfferService:
    return build_offer_service(db_session)


async def provide_partner_repository(db_session: NamedDependency[AsyncSession]) -> PartnerRepository:
    return PartnerRepository(session=db_session)


async def provide_offer_admin_service(
    db_session: NamedDependency[AsyncSession],
    translation_service: NamedDependency[TranslationService],
) -> OfferAdminService:
    return OfferAdminService(
        OfferRepository(session=db_session),
        PartnerRepository(session=db_session),
        PointRepository(session=db_session),
        translation_service,
    )


async def provide_partner_admin_service(
    db_session: NamedDependency[AsyncSession],
    media_service: NamedDependency[MediaService],
    translation_service: NamedDependency[TranslationService],
) -> PartnerAdminService:
    return PartnerAdminService(
        PartnerRepository(session=db_session),
        PartnerMemberRepository(session=db_session),
        UserService(session=db_session),
        media_service,
        translation_service,
    )
