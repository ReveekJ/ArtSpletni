from enum import StrEnum

from sqlalchemy import Enum


def str_enum[E: StrEnum](enum_cls: type[E]) -> Enum:
    return Enum(
        enum_cls,
        native_enum=False,
        length=32,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )
