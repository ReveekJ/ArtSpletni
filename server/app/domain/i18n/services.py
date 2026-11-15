import logging
from collections.abc import Mapping, Sequence

from app.domain.i18n.providers import TranslationError, TranslationProvider
from app.lib.exceptions import BadRequestError, ServiceUnavailableError
from app.lib.i18n import LocalizedText, LocalizedValue

logger = logging.getLogger(__name__)


class TranslationService:
    def __init__(self, provider: TranslationProvider, languages: Sequence[str], source_language: str) -> None:
        self._provider = provider
        self._languages = tuple(languages)
        self._source = source_language

    @property
    def languages(self) -> tuple[str, ...]:
        return self._languages

    @property
    def source_language(self) -> str:
        return self._source

    async def localize(
        self,
        submitted: Mapping[str, str],
        previous: LocalizedText | None = None,
        *,
        required: bool = True,
    ) -> LocalizedText | None:
        result = self._merge_submitted(submitted, previous)
        if required and self._source not in result:
            raise BadRequestError(f"Text in '{self._source}' is required", code="source_text_required")
        pivot = self._pivot(result)
        if pivot is None:
            return result or None
        pivot_text = result[pivot].text
        previous_pivot = previous.get(pivot) if previous else None
        pivot_changed = previous_pivot is None or previous_pivot.text != pivot_text
        targets = [
            lang
            for lang in self._languages
            if lang != pivot and (lang not in result or (result[lang].machine and pivot_changed))
        ]
        for lang in targets:
            try:
                (translated,) = await self._provider.translate([pivot_text], pivot, lang)
            except TranslationError as exc:
                logger.warning("Machine translation to %s failed: %s", lang, exc)
                continue
            result[lang] = LocalizedValue(text=translated, machine=True)
        return result

    async def translate_texts(self, texts: list[str], targets: Sequence[str]) -> dict[str, list[str]]:
        unknown = set(targets) - set(self._languages)
        if unknown:
            raise BadRequestError(f"Unsupported languages: {sorted(unknown)}", code="unsupported_language")
        translated: dict[str, list[str]] = {}
        for lang in targets:
            try:
                translated[lang] = await self._provider.translate(texts, self._source, lang)
            except TranslationError as exc:
                raise ServiceUnavailableError(str(exc), code="translation_failed") from exc
        return translated

    async def translate_between(self, text: str, source: str, target: str) -> str:
        try:
            (translated,) = await self._provider.translate([text], source, target)
        except TranslationError as exc:
            raise ServiceUnavailableError(str(exc), code="translation_failed") from exc
        return translated

    def _pivot(self, result: LocalizedText) -> str | None:
        human = [lang for lang in self._languages if lang in result and not result[lang].machine]
        if self._source in human:
            return self._source
        if human:
            return human[0]
        return self._source if self._source in result else None

    def _merge_submitted(self, submitted: Mapping[str, str], previous: LocalizedText | None) -> LocalizedText:
        unknown = set(submitted) - set(self._languages)
        if unknown:
            raise BadRequestError(f"Unsupported languages: {sorted(unknown)}", code="unsupported_language")
        result: LocalizedText = {}
        for lang, raw in submitted.items():
            text = raw.strip()
            if not text:
                continue
            old = previous.get(lang) if previous else None
            machine = old is not None and old.machine and old.text == text
            result[lang] = LocalizedValue(text=text, machine=machine)
        return result
