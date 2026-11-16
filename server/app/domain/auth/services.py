from datetime import UTC, datetime

from app.db.models import User, UserKind
from app.domain.auth.merge import AccountMergeService
from app.domain.auth.yandex import YandexProfile
from app.domain.users.services import UserService, normalize_email
from app.lib.exceptions import ConflictError, ForbiddenError, UnauthorizedError
from app.lib.security import hash_password, verify_password


class AuthService:
    def __init__(self, users: UserService, merger: AccountMergeService) -> None:
        self._users = users
        self._merger = merger

    async def register(
        self, email: str, password: str, display_name: str | None, current: User | None
    ) -> User:
        normalized = normalize_email(email)
        if await self._users.get_by_email(normalized) is not None:
            raise ConflictError("Email is already registered", code="email_taken")
        password_hash = await hash_password(password)
        if current is not None and current.is_guest:
            current.email = normalized
            current.password_hash = password_hash
            current.display_name = display_name
            current.kind = UserKind.REGISTERED
            return await self._users.update(current)
        return await self._users.create(
            User(
                email=normalized,
                password_hash=password_hash,
                display_name=display_name,
                kind=UserKind.REGISTERED,
            )
        )

    async def authenticate(self, email: str, password: str, current: User | None) -> User:
        user = await self._users.get_by_email(email)
        is_valid = await verify_password(password, user.password_hash if user else None)
        if user is None or user.password_hash is None or not is_valid:
            raise UnauthorizedError("Invalid email or password", code="invalid_credentials")
        return await self.login_as(user, current)

    async def login_as(self, user: User, current: User | None) -> User:
        self._ensure_active(user)
        await self._merger.absorb_guest(current, user)
        return user

    async def login_with_yandex(self, profile: YandexProfile, current: User | None) -> User:
        user = await self._users.get_by_yandex_id(profile.id)
        email = normalize_email(profile.default_email) if profile.default_email else None
        if user is None and email is not None:
            user = await self._users.get_by_email(email)
            if user is not None:
                user.yandex_id = profile.id
                user.email_verified_at = user.email_verified_at or datetime.now(UTC)
                user = await self._users.update(user)
        if user is not None:
            self._ensure_active(user)
            await self._merger.absorb_guest(current, user)
            return user
        target = current if current is not None and current.is_guest else User()
        target.yandex_id = profile.id
        target.email = email
        target.display_name = profile.display_name or profile.real_name
        target.kind = UserKind.REGISTERED
        target.email_verified_at = datetime.now(UTC) if email else None
        if target is current:
            return await self._users.update(target)
        return await self._users.create(target)

    @staticmethod
    def _ensure_active(user: User) -> None:
        if not user.is_active:
            raise ForbiddenError("Account is disabled", code="account_disabled")
