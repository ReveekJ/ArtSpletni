"""
Storage fixtures for pytest.

Replaces the external MinIO service with a FakeStorageService.
All business logic (services, repositories, endpoints) runs real;
only S3 presign/upload/delete are stubbed.
"""

from typing import AsyncGenerator

import pytest

from app.services import storage_service as storage_module
from app.services.storage_service import StorageService


class FakeStorageService(StorageService):
    """
    Drop-in replacement for StorageService that does not touch MinIO.
    presign_get returns a deterministic dummy URL.
    upload and delete are no-ops.
    """

    def presign_get(self, s3_key: str, expires_seconds: int | None = None) -> str:
        return f"http://test-minio.local/{s3_key}"

    def upload(self, s3_key: str, data: bytes, content_type: str) -> None:
        pass

    def delete(self, s3_key: str) -> None:
        pass


@pytest.fixture(autouse=True, scope="session")
def setup_fake_storage() -> AsyncGenerator[None, None]:
    """Replace the global storage singleton with FakeStorageService."""
    fake = FakeStorageService()
    storage_module._storage = fake
    yield
    storage_module._storage = None
