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
    minio_secure: bool = False
    presign_expires_seconds: int = 86400

    admin_username: str = "admin"
    admin_password: str = "admin-spletni"
    session_secret: str = "dev-session-secret-change-me"

    public_base_url: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
