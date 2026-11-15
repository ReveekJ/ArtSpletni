from datetime import timedelta
from functools import lru_cache, partial

from advanced_alchemy.extensions.litestar import (
    AlembicAsyncConfig,
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
)
from advanced_alchemy.extensions.litestar.store import SQLAlchemyStore
from litestar import Request
from litestar.datastructures import State
from litestar.middleware.rate_limit import DurationUnit, RateLimitConfig, get_remote_address
from litestar.middleware.session.server_side import ServerSideSessionConfig
from litestar_email import EmailConfig, EmailService, SMTPConfig

from app.db.models import KeyValueStoreItem
from app.lib.settings import get_settings

SESSION_STORE = "sessions"
RATE_LIMIT_STORE = "rate_limit"
SESSION_COOKIE = "spletni_session"


@lru_cache(maxsize=1)
def alchemy_config() -> SQLAlchemyAsyncConfig:
    return SQLAlchemyAsyncConfig(
        connection_string=get_settings().database_url,
        before_send_handler="autocommit_include_redirects",
        session_config=AsyncSessionConfig(expire_on_commit=False),
        alembic_config=AlembicAsyncConfig(
            script_location="app/db/migrations",
            version_table_name="alembic_version",
        ),
    )


def build_stores() -> dict[str, SQLAlchemyStore[SQLAlchemyAsyncConfig]]:
    config = alchemy_config()
    return {
        SESSION_STORE: SQLAlchemyStore(config=config, model=KeyValueStoreItem, namespace=SESSION_STORE),
        RATE_LIMIT_STORE: SQLAlchemyStore(config=config, model=KeyValueStoreItem, namespace=RATE_LIMIT_STORE),
    }


def session_config() -> ServerSideSessionConfig:
    settings = get_settings()
    return ServerSideSessionConfig(
        store=SESSION_STORE,
        key=SESSION_COOKIE,
        max_age=int(timedelta(days=settings.session_max_age_days).total_seconds()),
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
        renew_on_access=True,
    )


def _bucket_identifier(bucket: str, request: Request[object, object, State]) -> str:
    return f"{bucket}:{get_remote_address(request)}"


def rate_limit(bucket: str, unit: DurationUnit, limit: int) -> RateLimitConfig:
    return RateLimitConfig(
        rate_limit=(unit, limit),
        store=RATE_LIMIT_STORE,
        identifier_for_request=partial(_bucket_identifier, bucket),
    )


def strict_rate_limit() -> RateLimitConfig:
    return rate_limit("auth", "minute", 10)


@lru_cache(maxsize=1)
def email_config() -> EmailConfig:
    settings = get_settings()
    if settings.smtp is None:
        return EmailConfig(
            backend=settings.mail_fallback_backend, from_email=settings.mail_from, from_name="Сплетни"
        )
    smtp = settings.smtp
    return EmailConfig(
        backend=SMTPConfig(
            host=smtp.host,
            port=smtp.port,
            username=smtp.username,
            password=smtp.password.get_secret_value() if smtp.password else None,
            use_tls=smtp.use_tls,
            use_ssl=smtp.use_ssl,
        ),
        from_email=settings.mail_from,
        from_name="Сплетни",
    )


async def provide_email_service() -> EmailService:
    return EmailService(email_config())
