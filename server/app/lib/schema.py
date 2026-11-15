import msgspec


class CamelizedBaseStruct(msgspec.Struct, rename="camel", kw_only=True):
    pass
