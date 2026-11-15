import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from litestar_email import EmailMessage, EmailService
from sqlalchemy import update

from app.db.models import PasswordResetToken
from app.domain.users.services import UserService
from app.lib.exceptions import BadRequestError
from app.lib.security import generate_token, hash_password, hash_token

logger = logging.getLogger(__name__)

TOKEN_TTL = timedelta(hours=1)


class PasswordResetTokenRepository(SQLAlchemyAsyncRepository[PasswordResetToken]):
    model_type = PasswordResetToken

    async def invalidate_for_user(self, user_id: UUID, now: datetime) -> None:
        await self.session.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.user_id == user_id, PasswordResetToken.used_at.is_(None))
            .values(used_at=now)
        )


class PasswordResetService:
    def __init__(
        self,
        users: UserService,
        tokens: PasswordResetTokenRepository,
        mailer: EmailService,
        public_base_url: str,
    ) -> None:
        self._users = users
        self._tokens = tokens
        self._mailer = mailer
        self._public_base_url = public_base_url.rstrip("/")

    async def request_reset(self, email: str) -> None:
        user = await self._users.get_by_email(email)
        if user is None or user.email is None or user.is_guest or not user.is_active:
            return
        now = datetime.now(UTC)
        await self._tokens.invalidate_for_user(user.id, now)
        token = generate_token()
        await self._tokens.add(
            PasswordResetToken(user_id=user.id, token_hash=hash_token(token), expires_at=now + TOKEN_TTL)
        )
        link = f"{self._public_base_url}/reset-password?token={token}"
        await self._mailer.send_message(
            EmailMessage(
                subject="Сплетни: восстановление пароля",
                body=f"Чтобы задать новый пароль, перейдите по ссылке (действует 1 час):\n{link}",
                to=[user.email],
            )
        )
        logger.info("Password reset requested for user %s", user.id)

    async def confirm_reset(self, token: str, password: str) -> None:
        now = datetime.now(UTC)
        record = await self._tokens.get_one_or_none(token_hash=hash_token(token))
        if record is None or record.used_at is not None or record.expires_at <= now:
            raise BadRequestError("Reset link is invalid or expired", code="invalid_reset_token")
        user = await self._users.get(record.user_id)
        user.password_hash = await hash_password(password)
        await self._users.update(user)
        await self._tokens.invalidate_for_user(user.id, now)
