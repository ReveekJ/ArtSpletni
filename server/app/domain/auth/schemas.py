from datetime import datetime
from typing import Annotated
from uuid import UUID

import msgspec

from app.db.models import User, UserKind, UserRole
from app.lib.schema import CamelizedBaseStruct

Email = Annotated[str, msgspec.Meta(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=320)]
Password = Annotated[str, msgspec.Meta(min_length=8, max_length=128)]
DisplayName = Annotated[str, msgspec.Meta(min_length=1, max_length=100)]


class RegisterPayload(CamelizedBaseStruct):
    email: Email
    password: Password
    display_name: DisplayName | None = None


class LoginPayload(CamelizedBaseStruct):
    email: Email
    password: Annotated[str, msgspec.Meta(max_length=128)]


class PasswordResetRequestPayload(CamelizedBaseStruct):
    email: Email


class PasswordResetConfirmPayload(CamelizedBaseStruct):
    token: Annotated[str, msgspec.Meta(min_length=16, max_length=128)]
    password: Password


class UserProfile(CamelizedBaseStruct):
    id: UUID
    email: str | None
    display_name: str | None
    kind: UserKind
    role: UserRole
    created_at: datetime

    @classmethod
    def from_model(cls, user: User) -> "UserProfile":
        return cls(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            kind=user.kind,
            role=user.role,
            created_at=user.created_at,
        )


class SessionState(CamelizedBaseStruct):
    user: UserProfile | None


class AuthorizeUrl(CamelizedBaseStruct):
    url: str
