from typing import Protocol

from google.api_core.exceptions import GoogleAPIError
from google.cloud.translate_v3 import TranslateTextRequest, TranslationServiceAsyncClient
from google.oauth2 import service_account

from app.lib.settings import GoogleTranslateSettings


class TranslationError(Exception):
    pass


class TranslationProvider(Protocol):
    async def translate(self, texts: list[str], source: str, target: str) -> list[str]: ...


class DisabledTranslationProvider:
    async def translate(self, texts: list[str], source: str, target: str) -> list[str]:
        raise TranslationError("Machine translation is not configured")


class GoogleTranslationProvider:
    def __init__(self, settings: GoogleTranslateSettings) -> None:
        self._settings = settings
        self._client: TranslationServiceAsyncClient | None = None

    def _get_client(self) -> TranslationServiceAsyncClient:
        if self._client is None:
            credentials = service_account.Credentials.from_service_account_file(  # type: ignore[no-untyped-call]
                str(self._settings.credentials_file)
            )
            self._client = TranslationServiceAsyncClient(credentials=credentials)
        return self._client

    async def translate(self, texts: list[str], source: str, target: str) -> list[str]:
        request = TranslateTextRequest(
            parent=f"projects/{self._settings.project_id}/locations/{self._settings.location}",
            contents=texts,
            mime_type="text/plain",
            source_language_code=source,
            target_language_code=target,
        )
        try:
            response = await self._get_client().translate_text(request=request)
        except GoogleAPIError as exc:
            raise TranslationError(str(exc)) from exc
        return [item.translated_text for item in response.translations]
