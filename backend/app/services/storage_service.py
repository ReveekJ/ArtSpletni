import io
from datetime import timedelta

from minio import Minio

from app.core.config import get_settings


class StorageService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: Minio | None = None
        self._public_client: Minio | None = None

    @property
    def client(self) -> Minio:
        if self._client is None:
            self._client = Minio(
                self._settings.minio_endpoint_internal,
                access_key=self._settings.minio_access_key,
                secret_key=self._settings.minio_secret_key,
                secure=self._settings.minio_secure,
                region="us-east-1",
            )
            self._ensure_bucket()
        return self._client

    @property
    def public_client(self) -> Minio:
        if self._public_client is None:
            self._public_client = Minio(
                self._settings.minio_endpoint_public,
                access_key=self._settings.minio_access_key,
                secret_key=self._settings.minio_secret_key,
                secure=self._settings.minio_secure,
                region="us-east-1",
            )
        return self._public_client

    def _ensure_bucket(self) -> None:
        bucket = self._settings.minio_bucket
        if not self._client.bucket_exists(bucket):
            self._client.make_bucket(bucket)

    def upload(self, s3_key: str, data: bytes, content_type: str) -> None:
        self.client.put_object(
            self._settings.minio_bucket,
            s3_key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    def delete(self, s3_key: str) -> None:
        self.client.remove_object(self._settings.minio_bucket, s3_key)

    def presign_get(self, s3_key: str) -> str:
        return self.public_client.presigned_get_object(
            self._settings.minio_bucket,
            s3_key,
            expires=timedelta(seconds=self._settings.presign_expires_seconds),
        )


_storage: StorageService | None = None


def get_storage() -> StorageService:
    global _storage
    if _storage is None:
        _storage = StorageService()
    return _storage
