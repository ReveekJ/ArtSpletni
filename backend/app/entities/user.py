from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    yandex_id: Mapped[str | None] = mapped_column(
        String(64), unique=True, index=True, nullable=True,
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False,
    )
