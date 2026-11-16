from collections.abc import Sequence
from dataclasses import dataclass

from app.db.models import User, UserRole
from app.domain.users.services import UserService
from app.lib.exceptions import NotFoundError

DEMO_EMAIL_DOMAIN = "demo.spletni.local"
DEMO_PARTNER_NAME = "Кофейня «Сплетница» (демо)"


@dataclass(frozen=True, slots=True)
class DemoAccount:
    key: str
    display_name: str
    role: UserRole = UserRole.PLAYER
    is_partner: bool = False

    @property
    def email(self) -> str:
        return f"{self.key}@{DEMO_EMAIL_DOMAIN}"


DEMO_ACCOUNTS: tuple[DemoAccount, ...] = (
    DemoAccount(key="admin", display_name="Админ Сплетен", role=UserRole.ADMIN),
    DemoAccount(key="partner", display_name="Бариста из «Сплетницы»", is_partner=True),
    DemoAccount(key="anna", display_name="Аня, новичок"),
    DemoAccount(key="boris", display_name="Борис, краевед"),
    DemoAccount(key="tourist", display_name="Emma, tourist"),
)


class DemoAccountService:
    def __init__(self, users: UserService) -> None:
        self._users = users

    async def available(self) -> Sequence[DemoAccount]:
        emails = [account.email for account in DEMO_ACCOUNTS]
        existing = {
            user.email
            for user in await self._users.get_many(User.email.in_(emails), User.is_active.is_(True))
        }
        return [account for account in DEMO_ACCOUNTS if account.email in existing]

    async def get_user(self, key: str) -> User:
        account = next((item for item in DEMO_ACCOUNTS if item.key == key), None)
        user = await self._users.get_by_email(account.email) if account else None
        if user is None:
            raise NotFoundError("Demo account not found", code="demo_account_not_found")
        return user
