from typing import Annotated

import msgspec

from app.lib.i18n import LocalizedText, LocalizedValue
from app.lib.schema import CamelizedBaseStruct

LocalizedInput = dict[str, Annotated[str, msgspec.Meta(max_length=20000)]]


class LocalizedField(CamelizedBaseStruct):
    text: str
    machine: bool


def localized_out(value: LocalizedText | None) -> dict[str, LocalizedField]:
    if not value:
        return {}
    return {lang: LocalizedField(text=item.text, machine=item.machine) for lang, item in value.items()}


class TranslateRequest(CamelizedBaseStruct):
    texts: Annotated[
        list[Annotated[str, msgspec.Meta(max_length=20000)]], msgspec.Meta(min_length=1, max_length=50)
    ]
    target_languages: Annotated[list[str], msgspec.Meta(min_length=1)]


class TranslateResponse(CamelizedBaseStruct):
    translations: dict[str, list[str]]


class LanguageSettings(CamelizedBaseStruct):
    languages: list[str]
    default_language: str


__all__ = ("LocalizedField", "LocalizedInput", "LocalizedValue", "localized_out")
