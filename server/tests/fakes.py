from dataclasses import dataclass
from datetime import timedelta

import msgspec

from app.domain.gossip.llm_schema import LlmGossipResponse
from app.domain.gossip.types import CommonsPhoto, GossipSubject, NearbyContext, WikiPlace
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


class FakeNearbySource:
    def __init__(self) -> None:
        self.calls: list[tuple[float, float]] = []

    async def collect(self, latitude: float, longitude: float, radius_m: int, limit: int) -> NearbyContext:
        self.calls.append((latitude, longitude))
        return NearbyContext(
            places=[
                WikiPlace(
                    ref="P1",
                    title="Old Tower",
                    language="en",
                    url="https://en.wikipedia.org/wiki/Old_Tower",
                    extract="An old tower.",
                    latitude=56.84,
                    longitude=60.61,
                    distance_m=120,
                    page_image="Old_tower.jpg",
                )
            ],
            photos=[
                CommonsPhoto(
                    ref="I1",
                    file_title="File:Old_tower.jpg",
                    description="Old tower at dusk",
                    url="https://upload.wikimedia.org/old_tower_800.jpg",
                    author="Jane Doe",
                    license="CC BY-SA 4.0",
                    source_url="https://commons.wikimedia.org/wiki/File:Old_tower.jpg",
                    latitude=56.84,
                    longitude=60.61,
                    distance_m=118,
                )
            ],
        )


def _llm_response() -> LlmGossipResponse:
    def texts(prefix: str) -> dict[str, dict[str, str]]:
        return {
            lang: {"title": f"{prefix} {lang}", "text": f"{prefix} text {lang}"}
            for lang in ("ru", "en", "zh")
        }

    return msgspec.convert(
        {
            "items": [
                {
                    "category": "mystic",
                    "veracity": "legend",
                    "place_ref": "P1",
                    "photo_ref": "I1",
                    "source_refs": ["P1"],
                    "extra_links": [
                        {"url": "https://example.com/alive", "title": "Alive"},
                        {"url": "https://example.com/dead", "title": "Dead"},
                    ],
                    "localizations": texts("Ghost"),
                },
                {
                    "category": "romance",
                    "veracity": "documented",
                    "place_name": "Bench by the river",
                    "photo_ref": "I999",
                    "localizations": texts("Kiss"),
                },
            ]
        },
        type=LlmGossipResponse,
    )


class FakeGossipWriter:
    def __init__(self) -> None:
        self.calls = 0
        self.error: Exception | None = None

    async def write(
        self, subject: GossipSubject, context: NearbyContext, max_items: int, languages: list[str]
    ) -> LlmGossipResponse:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return _llm_response()


class FakeLinkChecker:
    async def filter_alive(self, urls: list[str]) -> set[str]:
        return {url for url in urls if url.endswith("/alive")}


@dataclass
class GossipFakes:
    nearby: FakeNearbySource
    writer: FakeGossipWriter
    links: FakeLinkChecker
