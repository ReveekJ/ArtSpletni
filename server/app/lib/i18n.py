import msgspec
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class LocalizedValue(msgspec.Struct, kw_only=True, frozen=True):
    text: str
    machine: bool = False


LocalizedText = dict[str, LocalizedValue]

_RawLocalized = dict[str, dict[str, str | bool]]


def resolve_text(value: LocalizedText | None, language: str, fallback: str) -> str | None:
    if not value:
        return None
    for lang in (language, fallback):
        item = value.get(lang)
        if item is not None and item.text:
            return item.text
    return next((item.text for item in value.values() if item.text), None)


class LocalizedTextType(TypeDecorator[LocalizedText]):
    impl = JSONB
    cache_ok = True

    def process_bind_param(self, value: LocalizedText | None, dialect: Dialect) -> _RawLocalized | None:
        if value is None:
            return None
        raw: _RawLocalized = msgspec.to_builtins(value)
        return raw

    def process_result_value(self, value: _RawLocalized | None, dialect: Dialect) -> LocalizedText | None:
        if value is None:
            return None
        return msgspec.convert(value, type=LocalizedText)
