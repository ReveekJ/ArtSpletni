from app.db.models import GossipItem
from app.domain.gossip.schemas import (
    AdminGossipItemOut,
    GossipItemOut,
    GossipPhotoOut,
    GossipSourceOut,
    GossipTextOut,
)
from app.lib.i18n import resolve_text


def _photo(item: GossipItem) -> GossipPhotoOut | None:
    if not item.photo_url:
        return None
    return GossipPhotoOut(
        url=item.photo_url,
        author=item.photo_author,
        license=item.photo_license,
        source_url=item.photo_source_url,
    )


def _sources(item: GossipItem) -> list[GossipSourceOut]:
    return [
        GossipSourceOut(url=source.url, title=source.title, origin=source.origin) for source in item.sources
    ]


def gossip_item_out(item: GossipItem, language: str, fallback: str) -> GossipItemOut:
    return GossipItemOut(
        id=item.id,
        title=resolve_text(item.title, language, fallback) or "",
        text=resolve_text(item.text, language, fallback) or "",
        category=item.category,
        veracity=item.veracity,
        place_name=item.place_name,
        distance_m=item.distance_m,
        photo=_photo(item),
        sources=_sources(item),
    )


def admin_gossip_item_out(item: GossipItem, language: str, fallback: str) -> AdminGossipItemOut:
    return AdminGossipItemOut(
        id=item.id,
        title=resolve_text(item.title, language, fallback) or "",
        text=resolve_text(item.text, language, fallback) or "",
        category=item.category,
        veracity=item.veracity,
        place_name=item.place_name,
        distance_m=item.distance_m,
        photo=_photo(item),
        sources=_sources(item),
        is_hidden=item.is_hidden,
        translations={
            lang: GossipTextOut(title=value.text, text=item.text[lang].text if lang in item.text else "")
            for lang, value in item.title.items()
        },
    )
