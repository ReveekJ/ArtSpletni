from datetime import datetime
from enum import StrEnum

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.types import str_enum


class UserKind(StrEnum):
    GUEST = "guest"
    REGISTERED = "registered"


class UserRole(StrEnum):
    PLAYER = "player"
    ADMIN = "admin"


class User(UUIDv7AuditBase):
    __tablename__ = "users"

    email: Mapped[str | None] = mapped_column(String(320), unique=True, default=None)
    password_hash: Mapped[str | None] = mapped_column(String(255), default=None)
    yandex_id: Mapped[str | None] = mapped_column(String(64), unique=True, default=None)
    display_name: Mapped[str | None] = mapped_column(String(100), default=None)
    kind: Mapped[UserKind] = mapped_column(str_enum(UserKind), default=UserKind.GUEST)
    role: Mapped[UserRole] = mapped_column(str_enum(UserRole), default=UserRole.PLAYER)
    is_active: Mapped[bool] = mapped_column(default=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), default=None)

    @property
    def is_guest(self) -> bool:
        return self.kind is UserKind.GUEST

    @property
    def is_admin(self) -> bool:
        return self.role is UserRole.ADMIN
