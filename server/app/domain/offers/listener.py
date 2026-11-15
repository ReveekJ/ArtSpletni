from collections.abc import Sequence

from app.domain.offers.services import OfferService
from app.domain.runs.events import Notification, PointUnlocked, ProgressEvent
from app.lib.i18n import resolve_text


class OfferProgressListener:
    def __init__(self, offers: OfferService, language: str, fallback: str) -> None:
        self._offers = offers
        self._language = language
        self._fallback = fallback

    async def handle(self, event: ProgressEvent) -> Sequence[Notification]:
        if not isinstance(event, PointUnlocked):
            return ()
        offer = await self._offers.offer_for_point(event.point_id)
        if offer is None:
            return ()
        grant = await self._offers.grant(event.user_id, offer, event.at)
        if grant is None:
            return ()
        return (
            Notification(
                kind="offer_granted",
                id=grant.id,
                title=resolve_text(offer.title, self._language, self._fallback),
            ),
        )
