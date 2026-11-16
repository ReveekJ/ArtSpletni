from datetime import timedelta
from functools import lru_cache
from typing import Protocol

import obstore
from obstore.exceptions import NotFoundError as ObjectNotFoundError
from obstore.store import S3Store

from app.lib.settings import S3Settings, get_settings


class ObjectStorage(Protocol):
    async def presign_upload(self, key: str, expires_in: timedelta) -> str: ...

    async def presign_download(self, key: str, expires_in: timedelta) -> str: ...

    async def object_size(self, key: str) -> int | None: ...

    async def put(self, key: str, data: bytes, content_type: str) -> None: ...

    async def delete(self, key: str) -> None: ...


def _store(settings: S3Settings, endpoint: str) -> S3Store:
    return S3Store(
        settings.bucket,
        endpoint=endpoint,
        access_key_id=settings.access_key.get_secret_value(),
        secret_access_key=settings.secret_key.get_secret_value(),
        region=settings.region,
        virtual_hosted_style_request=False,
        client_options={"allow_http": endpoint.startswith("http://")},
    )


class S3ObjectStorage:
    def __init__(self, settings: S3Settings) -> None:
        self._internal = _store(settings, settings.endpoint)
        self._public = _store(settings, settings.public_endpoint)

    async def presign_upload(self, key: str, expires_in: timedelta) -> str:
        return await obstore.sign_async(self._public, "PUT", key, expires_in)

    async def presign_download(self, key: str, expires_in: timedelta) -> str:
        return await obstore.sign_async(self._public, "GET", key, expires_in)

    async def object_size(self, key: str) -> int | None:
        try:
            meta = await obstore.head_async(self._internal, key)
        except (FileNotFoundError, ObjectNotFoundError):
            return None
        return meta["size"]

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        await obstore.put_async(self._internal, key, data, attributes={"Content-Type": content_type})

    async def delete(self, key: str) -> None:
        await obstore.delete_async(self._internal, key)


@lru_cache(maxsize=1)
def object_storage() -> ObjectStorage:
    return S3ObjectStorage(get_settings().s3)
