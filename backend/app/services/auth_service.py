from dataclasses import dataclass

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass(slots=True)
class UserDTO:
    id: int
    email: str
    display_name: str
    is_admin: bool


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register(self, email: str, password: str, display_name: str) -> User:
        existing = await self._get_by_email(email)
        if existing is not None:
            raise ValueError("Email already registered")
        user = User(
            email=email.lower().strip(),
            password_hash=pwd_context.hash(password),
            display_name=display_name.strip(),
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        user = await self._get_by_email(email)
        if user is None or user.password_hash is None:
            return None
        if not pwd_context.verify(password, user.password_hash):
            return None
        return user

    async def get_or_create_yandex_user(
        self, yandex_id: str, email: str, display_name: str,
    ) -> User:
        user = await self._get_by_yandex_id(yandex_id)
        if user is not None:
            return user
        existing = await self._get_by_email(email)
        if existing is not None:
            existing.yandex_id = yandex_id
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        user = User(
            email=email.lower().strip(),
            yandex_id=yandex_id,
            display_name=display_name.strip(),
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def list_all(self) -> list[User]:
        result = await self.session.execute(select(User).order_by(User.id.desc()))
        return list(result.scalars().all())

    async def _get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower().strip())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_by_yandex_id(self, yandex_id: str) -> User | None:
        stmt = select(User).where(User.yandex_id == yandex_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def to_dto(user: User) -> UserDTO:
        return UserDTO(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            is_admin=user.is_admin,
        )
