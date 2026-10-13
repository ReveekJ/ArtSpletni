from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://spletni:spletni@db:5432/test-spletni"

    minio_endpoint_internal: str = "minio:9000"
    minio_endpoint_public: str = "localhost:9000"
    minio_access_key: str = "spletni"
    minio_secret_key: str = "spletni-minio-secret"
    minio_bucket: str = "tracks"
    minio_secure_internal: bool = False
    minio_secure_public: bool = True
    presign_expires_seconds: int = 86400
    track_access_ttl_seconds: int = 1800
    track_access_cookie_secure: bool = False
    submission_max_audio_bytes: int = 10 * 1024 * 1024
    submission_max_image_bytes: int = 5 * 1024 * 1024
    submission_rate_limit: int = 5
    submission_rate_window_seconds: int = 3600

    admin_username: str = "admin"
    admin_password: str = "admin-spletni"
    session_secret: str = "dev-session-secret-change-me"

    db_guard_enabled: bool = True

    public_base_url: str = "http://localhost:5173"

    yandex_client_id: str = ""
    yandex_client_secret: str = ""
    yandex_redirect_uri: str = "http://localhost:5173/api/auth/yandex/callback"


@lru_cache
def get_settings() -> Settings:
    return Settings()
