from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class S3Settings(BaseModel):
    endpoint: str
    public_endpoint: str
    access_key: SecretStr
    secret_key: SecretStr
    bucket: str
    region: str = "us-east-1"


class YandexSettings(BaseModel):
    client_id: str
    client_secret: SecretStr
    redirect_uri: str


class SmtpSettings(BaseModel):
    host: str
    port: int = 587
    username: str | None = None
    password: SecretStr | None = None
    use_tls: bool = True
    use_ssl: bool = False


class GoogleTranslateSettings(BaseModel):
    project_id: str
    credentials_file: Path
    location: str = "global"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    database_url: str
    secret_key: SecretStr = Field(min_length=32)
    public_base_url: str
    cors_allowed_origins: list[str] = Field(default_factory=list)
    session_max_age_days: int = 60
    session_cookie_secure: bool = True
    languages: list[str] = Field(default_factory=lambda: ["ru", "en", "zh"])
    default_language: str = "ru"
    timezone: str = "Europe/Moscow"
    mail_from: str = "noreply@spletni.local"
    mail_fallback_backend: Literal["console", "memory"] = "console"
    s3: S3Settings
    yandex: YandexSettings | None = None
    smtp: SmtpSettings | None = None
    google_translate: GoogleTranslateSettings | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
