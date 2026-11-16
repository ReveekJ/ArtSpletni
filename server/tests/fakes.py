from datetime import timedelta

from app.domain.i18n.providers import TranslationError


class FakeObjectStorage:
    def __init__(self) -> None:
        self.objects: dict[str, int] = {}
        self.deleted: list[str] = []

    async def presign_upload(self, key: str, expires_in: timedelta) -> str:
        return f"https://storage.test/upload/{key}"

    async def presign_download(self, key: str, expires_in: timedelta) -> str:
        return f"https://storage.test/download/{key}?ttl={int(expires_in.total_seconds())}"

    async def object_size(self, key: str) -> int | None:
        return self.objects.get(key)

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        self.objects[key] = len(data)

    async def delete(self, key: str) -> None:
        self.objects.pop(key, None)
        self.deleted.append(key)


class FakeTranslationProvider:
    def __init__(self) -> None:
        self.failing_targets: set[str] = set()
        self.calls: list[tuple[str, str]] = []

    async def translate(self, texts: list[str], source: str, target: str) -> list[str]:
        self.calls.append((source, target))
        if target in self.failing_targets:
            raise TranslationError(f"{target} unavailable")
        return [f"[{target}] {text}" for text in texts]
