import pytest

from app.domain.i18n.services import TranslationService
from app.lib.exceptions import BadRequestError
from app.lib.i18n import LocalizedValue, resolve_text
from tests.conftest import Client
from tests.fakes import FakeTranslationProvider

pytestmark = pytest.mark.i18n

LANGS = ("ru", "en", "zh")


def _service(provider: FakeTranslationProvider) -> TranslationService:
    return TranslationService(provider, LANGS, "ru")


async def test_missing_languages_are_machine_translated() -> None:
    result = await _service(FakeTranslationProvider()).localize({"ru": " Привет "})

    assert result == {
        "ru": LocalizedValue(text="Привет"),
        "en": LocalizedValue(text="[en] Привет", machine=True),
        "zh": LocalizedValue(text="[zh] Привет", machine=True),
    }


async def test_human_translation_is_never_overwritten() -> None:
    service = _service(FakeTranslationProvider())
    first = await service.localize({"ru": "Привет", "en": "Hello"})

    second = await service.localize({"ru": "Здравствуйте", "en": "Hello"}, first)

    assert second is not None
    assert second["en"] == LocalizedValue(text="Hello")
    assert second["zh"] == LocalizedValue(text="[zh] Здравствуйте", machine=True)


async def test_unchanged_machine_text_keeps_flag_and_is_not_retranslated() -> None:
    provider = FakeTranslationProvider()
    service = _service(provider)
    first = await service.localize({"ru": "Привет"})
    assert first is not None
    provider.calls.clear()

    second = await service.localize({lang: value.text for lang, value in first.items()}, first)

    assert second == first
    assert provider.calls == []


async def test_edited_machine_text_becomes_human() -> None:
    service = _service(FakeTranslationProvider())
    first = await service.localize({"ru": "Привет"})

    second = await service.localize({"ru": "Привет", "en": "Hi there", "zh": "[zh] Привет"}, first)

    assert second is not None
    assert second["en"] == LocalizedValue(text="Hi there")
    assert second["zh"].machine is True


async def test_provider_failure_leaves_language_missing() -> None:
    provider = FakeTranslationProvider()
    provider.failing_targets.add("zh")

    result = await _service(provider).localize({"ru": "Привет"})

    assert result is not None
    assert "zh" not in result
    assert result["en"].machine is True


async def test_source_text_is_required() -> None:
    with pytest.raises(BadRequestError):
        await _service(FakeTranslationProvider()).localize({"en": "Hello"})
    assert await _service(FakeTranslationProvider()).localize({}, required=False) is None


def test_resolve_text_falls_back() -> None:
    value = {"ru": LocalizedValue(text="Привет"), "en": LocalizedValue(text="")}
    assert resolve_text(value, "en", "ru") == "Привет"
    assert resolve_text(None, "en", "ru") is None


async def test_admin_translate_endpoint(admin_client: Client, translator: FakeTranslationProvider) -> None:
    response = await admin_client.post(
        "/api/admin/translations", json={"texts": ["Сплетня"], "targetLanguages": ["en"]}
    )
    assert response.status_code == 200
    assert response.json() == {"translations": {"en": ["[en] Сплетня"]}}

    translator.failing_targets.add("zh")
    failed = await admin_client.post(
        "/api/admin/translations", json={"texts": ["Сплетня"], "targetLanguages": ["zh"]}
    )
    assert failed.status_code == 503


async def test_languages_endpoint(client: Client) -> None:
    response = await client.get("/api/languages")
    assert response.json() == {"languages": ["ru", "en", "zh"], "defaultLanguage": "ru"}
