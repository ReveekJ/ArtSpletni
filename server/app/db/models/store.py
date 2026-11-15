from advanced_alchemy.extensions.litestar.store import StoreModelMixin


class KeyValueStoreItem(StoreModelMixin):
    __tablename__ = "kv_store"
