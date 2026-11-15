from uuid import UUID

from app.domain.offers.repositories import OfferGrantRepository


class OfferGrantMerger:
    def __init__(self, grants: OfferGrantRepository) -> None:
        self._grants = grants

    async def merge_guest(self, guest_id: UUID, target_id: UUID) -> None:
        target_offers = {grant.offer_id: grant for grant in await self._grants.for_user(target_id)}
        for grant in await self._grants.for_user(guest_id):
            existing = target_offers.get(grant.offer_id)
            if existing is None:
                grant.user_id = target_id
                await self._grants.update(grant, auto_refresh=False)
            elif existing.redeemed_at is None and grant.redeemed_at is not None:
                await self._grants.delete(existing.id)
                grant.user_id = target_id
                await self._grants.update(grant, auto_refresh=False)
            else:
                await self._grants.delete(grant.id)
