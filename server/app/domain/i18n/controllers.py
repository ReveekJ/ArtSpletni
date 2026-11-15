from litestar import Controller, get, post
from litestar.di import NamedDependency
from litestar.params import JSONBody
from litestar.status_codes import HTTP_200_OK

from app.domain.auth.guards import requires_admin
from app.domain.i18n.schemas import LanguageSettings, TranslateRequest, TranslateResponse
from app.domain.i18n.services import TranslationService
from app.lib.settings import get_settings


class LanguagesController(Controller):
    path = "/api/languages"
    tags = ["I18n"]

    @get("/", summary="Supported languages", description="Content languages and the source language.")
    async def list_languages(self) -> LanguageSettings:
        settings = get_settings()
        return LanguageSettings(languages=settings.languages, default_language=settings.default_language)


class AdminTranslationController(Controller):
    path = "/api/admin/translations"
    tags = ["Admin: I18n"]
    guards = [requires_admin]

    @post(
        "/",
        summary="Machine-translate texts",
        description="Translate texts from the source language into the requested languages.",
        status_code=HTTP_200_OK,
    )
    async def translate(
        self,
        data: JSONBody[TranslateRequest],
        translation_service: NamedDependency[TranslationService],
    ) -> TranslateResponse:
        translations = await translation_service.translate_texts(data.texts, data.target_languages)
        return TranslateResponse(translations=translations)
