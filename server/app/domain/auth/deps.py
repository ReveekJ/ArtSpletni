from collections.abc import Sequence

import httpx
from litestar.di import NamedDependency
from litestar_email import EmailService
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.achievements.merge import AchievementMerger
from app.domain.achievements.services import UserAchievementRepository
from app.domain.auth.merge import AccountMergeService, GuestDataMerger
from app.domain.auth.password_reset import PasswordResetService, PasswordResetTokenRepository
from app.domain.auth.services import AuthService
from app.domain.auth.yandex import YandexOAuthClient
from app.domain.offers.merge import OfferGrantMerger
from app.domain.offers.repositories import OfferGrantRepository
from app.domain.runs.merge import GuestProgressMerger
from app.domain.runs.repositories import GuestProgressRepository, RunRepository
from app.domain.users.services import UserService
from app.lib.exceptions import ServiceUnavailableError
from app.lib.settings import get_settings


async def provide_users_service(db_session: NamedDependency[AsyncSession]) -> UserService:
    return UserService(session=db_session)


async def provide_guest_mergers(db_session: NamedDependency[AsyncSession]) -> Sequence[GuestDataMerger]:
    return (
        GuestProgressMerger(GuestProgressRepository(RunRepository(session=db_session))),
        OfferGrantMerger(OfferGrantRepository(session=db_session)),
        AchievementMerger(UserAchievementRepository(session=db_session)),
    )


async def provide_account_merge_service(
    users_service: NamedDependency[UserService], guest_mergers: NamedDependency[Sequence[GuestDataMerger]]
) -> AccountMergeService:
    return AccountMergeService(users_service, guest_mergers)


async def provide_auth_service(
    users_service: NamedDependency[UserService], account_merge_service: NamedDependency[AccountMergeService]
) -> AuthService:
    return AuthService(users_service, account_merge_service)


async def provide_password_reset_service(
    db_session: NamedDependency[AsyncSession],
    users_service: NamedDependency[UserService],
    email_service: NamedDependency[EmailService],
) -> PasswordResetService:
    return PasswordResetService(
        users=users_service,
        tokens=PasswordResetTokenRepository(session=db_session),
        mailer=email_service,
        public_base_url=get_settings().public_base_url,
    )


async def provide_yandex_client(http_client: NamedDependency[httpx.AsyncClient]) -> YandexOAuthClient:
    settings = get_settings().yandex
    if settings is None:
        raise ServiceUnavailableError("Yandex ID login is not configured", code="yandex_disabled")
    return YandexOAuthClient(settings, http_client)
