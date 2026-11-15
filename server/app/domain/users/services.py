from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from app.db.models import User, UserKind


class UserRepository(SQLAlchemyAsyncRepository[User]):
    model_type = User


class UserService(SQLAlchemyAsyncRepositoryService[User, UserRepository]):
    repository_type = UserRepository

    async def get_by_email(self, email: str) -> User | None:
        return await self.get_one_or_none(email=normalize_email(email))

    async def get_by_yandex_id(self, yandex_id: str) -> User | None:
        return await self.get_one_or_none(yandex_id=yandex_id)

    async def create_guest(self) -> User:
        return await self.create(User(kind=UserKind.GUEST))


def normalize_email(email: str) -> str:
    return email.strip().lower()
