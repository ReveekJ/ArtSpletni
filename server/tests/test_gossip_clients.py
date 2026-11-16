import json
from collections.abc import Callable

import httpx
import pytest
from pydantic import JsonValue, SecretStr

from app.domain.gossip.llm import GossipWriterError, LlmGossipWriter
from app.domain.gossip.types import GossipSubject, NearbyContext
from app.domain.gossip.wiki import WikiGeoClient, html_to_text
from app.lib.settings import LlmSettings

pytestmark = pytest.mark.gossip

Handler = Callable[[httpx.Request], httpx.Response]

SUBJECT = GossipSubject(title="Башня", location_name="ул. Ленина", latitude=56.84, longitude=60.6)
STORY = {
    "category": "fun",
    "veracity": "legend",
    "localizations": {"ru": {"title": "Т", "text": "Текст"}, "en": {"title": "T", "text": "Text"}},
}


def _mock_client(monkeypatch: pytest.MonkeyPatch, handler: Handler) -> None:
    real_client = httpx.AsyncClient

    def factory(**kwargs: object) -> httpx.AsyncClient:
        return real_client(transport=httpx.MockTransport(handler), **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr("app.domain.gossip.llm.httpx.AsyncClient", factory)
    monkeypatch.setattr("app.domain.gossip.wiki.httpx.AsyncClient", factory)


def _completion(content: str) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def _writer(extra_body: dict[str, JsonValue] | None = None, json_mode: bool = True) -> LlmGossipWriter:
    settings = LlmSettings(
        base_url="http://llm.test/v1/",
        model="m",
        api_key=SecretStr("secret"),
        json_mode=json_mode,
        extra_body=extra_body or {},
    )
    return LlmGossipWriter(settings)


async def test_writer_sends_openai_compatible_request(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _completion("Sure:\n```json\n" + json.dumps({"items": [STORY]}) + "\n```")

    _mock_client(monkeypatch, handler)

    response = await _writer(extra_body={"web_search": True}).write(SUBJECT, NearbyContext(), 3, ["ru", "en"])

    assert [item.category.value for item in response.items] == ["fun"]
    request = seen[0]
    body = json.loads(request.content)
    assert str(request.url) == "http://llm.test/v1/chat/completions"
    assert request.headers["authorization"] == "Bearer secret"
    assert body["model"] == "m"
    assert body["response_format"] == {"type": "json_object"}
    assert body["web_search"] is True
    assert "ru, en" in body["messages"][0]["content"]
    assert json.loads(body["messages"][1]["content"])["point"]["title"] == "Башня"


async def test_writer_retries_invalid_json_once(monkeypatch: pytest.MonkeyPatch) -> None:
    answers = iter(['{"items": [{"category": "bogus"}]}', json.dumps({"items": [STORY]})])
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _completion(next(answers))

    _mock_client(monkeypatch, handler)

    response = await _writer(json_mode=False).write(SUBJECT, NearbyContext(), 3, ["ru"])

    assert len(response.items) == 1
    assert "response_format" not in json.loads(requests[0].content)
    assert json.loads(requests[1].content)["messages"][-1]["content"].startswith("The JSON is invalid")


@pytest.mark.parametrize(
    "handler",
    [
        lambda request: httpx.Response(500, text="boom"),
        lambda request: httpx.Response(200, json={"choices": []}),
        lambda request: _completion("not json at all"),
    ],
)
async def test_writer_failures_raise(monkeypatch: pytest.MonkeyPatch, handler: Handler) -> None:
    _mock_client(monkeypatch, handler)

    with pytest.raises(GossipWriterError):
        await _writer().write(SUBJECT, NearbyContext(), 3, ["ru"])


def _wiki_handler(request: httpx.Request) -> httpx.Response:
    if request.url.host.endswith("wikipedia.org"):
        language = request.url.host.split(".")[0]
        return httpx.Response(
            200,
            json={
                "query": {
                    "pages": [
                        {
                            "title": f"Tower {language}",
                            "fullurl": f"https://{language}.wikipedia.org/wiki/Tower",
                            "extract": "An old tower.",
                            "pageimage": "Tower.jpg",
                            "coordinates": [{"lat": 56.84, "lon": 60.6, "dist": 120.4}],
                        },
                        {"title": "Ghost page", "missing": True},
                    ]
                }
            },
        )
    jpeg = {
        "title": "File:Tower.jpg",
        "coordinates": [{"lat": 56.84, "lon": 60.6, "dist": 12.6}],
        "imageinfo": [
            {
                "thumburl": "https://upload.example/tower_800.jpg",
                "url": "https://upload.example/tower.jpg",
                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Tower.jpg",
                "mime": "image/jpeg",
                "extmetadata": {
                    "Artist": {"value": 'N. <a href="https://x">Jane</a>'},
                    "LicenseShortName": {"value": "CC0"},
                    "ImageDescription": {"value": "Old <b>tower</b>"},
                },
            }
        ],
    }
    svg = {
        "title": "File:Logo.svg",
        "imageinfo": [
            {"url": "https://u/logo.svg", "descriptionurl": "https://c/Logo", "mime": "image/svg+xml"}
        ],
    }
    return httpx.Response(200, json={"query": {"pages": [jpeg, jpeg, svg]}})


async def test_wiki_client_collects_places_and_deduplicated_photos(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_client(monkeypatch, _wiki_handler)

    context = await WikiGeoClient("test-agent", 5.0).collect(56.84, 60.6, 500, 4)

    assert [(place.ref, place.language, place.distance_m) for place in context.places] == [
        ("P1", "ru", 120),
        ("P2", "en", 120),
    ]
    assert context.places[0].url == "https://ru.wikipedia.org/wiki/Tower"
    assert len(context.photos) == 1
    photo = context.photos[0]
    assert (photo.ref, photo.author, photo.license, photo.description) == (
        "I1",
        "N. Jane",
        "CC0",
        "Old tower",
    )
    assert photo.url == "https://upload.example/tower_800.jpg"
    assert photo.distance_m == 13


async def test_wiki_client_survives_upstream_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_client(monkeypatch, lambda request: httpx.Response(503))

    context = await WikiGeoClient("test-agent", 5.0).collect(56.84, 60.6, 500, 4)

    assert context == NearbyContext()


def test_html_to_text_strips_markup() -> None:
    assert html_to_text('A <a href="x">link</a>\n and  <i>text</i>') == "A link and text"
