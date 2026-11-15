from functools import lru_cache
from typing import Annotated

from litestar.params import FromQuery, HeaderParameter

from app.domain.i18n.providers import (
    DisabledTranslationProvider,
    GoogleTranslationProvider,
    TranslationProvider,
)
from app.domain.i18n.services import TranslationService
from app.lib.settings import get_settings


@lru_cache(maxsize=1)
def translation_provider() -> TranslationProvider:
    settings = get_settings().google_translate
    if settings is None:
        return DisabledTranslationProvider()
    return GoogleTranslationProvider(settings)


async def provide_translation_service() -> TranslationService:
    settings = get_settings()
    return TranslationService(translation_provider(), settings.languages, settings.default_language)


async def provide_language(
    lang: FromQuery[str | None] = None,
    accept_language: Annotated[str | None, HeaderParameter(name="accept-language")] = None,
) -> str:
    settings = get_settings()
    candidates = [lang] if lang else []
    if accept_language:
        candidates.extend(part.split(";")[0].strip() for part in accept_language.split(","))
    for candidate in candidates:
        code = candidate[:2].lower()
        if code in settings.languages:
            return code
    return settings.default_language
