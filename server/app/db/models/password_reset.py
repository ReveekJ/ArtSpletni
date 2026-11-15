from datetime import datetime
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column


class PasswordResetToken(UUIDv7AuditBase):
    __tablename__ = "password_reset_tokens"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTimeUTC(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), default=None)
