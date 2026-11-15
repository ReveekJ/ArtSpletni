from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Offer, OfferGrant


class OfferRepository(SQLAlchemyAsyncRepository[Offer]):
    model_type = Offer

    async def lock(self, offer_id: UUID) -> Offer | None:
        result = await self.session.execute(
            select(Offer)
            .where(Offer.id == offer_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()


@dataclass(frozen=True, slots=True)
class GrantStats:
    offer_id: UUID
    granted: int
    redeemed: int


class OfferGrantRepository(SQLAlchemyAsyncRepository[OfferGrant]):
    model_type = OfferGrant

    async def insert_if_absent(
        self, offer_id: UUID, user_id: UUID, code: str, expires_at: datetime | None
    ) -> UUID | None:
        result = await self.session.execute(
            insert(OfferGrant)
            .values(offer_id=offer_id, user_id=user_id, redemption_code=code, expires_at=expires_at)
            .on_conflict_do_nothing(index_elements=[OfferGrant.offer_id, OfferGrant.user_id])
            .returning(OfferGrant.id)
        )
        return result.scalar_one_or_none()

    async def for_user(self, user_id: UUID) -> Sequence[OfferGrant]:
        return await self.get_many(OfferGrant.user_id == user_id, order_by=[(OfferGrant.created_at, True)])

    async def recent_redemptions(self, offer_ids: Sequence[UUID], limit: int) -> Sequence[OfferGrant]:
        if not offer_ids:
            return []
        return await self.get_many(
            OfferGrant.offer_id.in_(offer_ids),
            OfferGrant.redeemed_at.is_not(None),
            LimitOffset(limit=limit, offset=0),
            order_by=[(OfferGrant.redeemed_at, True)],
        )

    async def stats(self, offer_ids: Sequence[UUID]) -> dict[UUID, GrantStats]:
        if not offer_ids:
            return {}
        rows = await self.session.execute(
            select(OfferGrant.offer_id, func.count(), func.count(OfferGrant.redeemed_at))
            .where(OfferGrant.offer_id.in_(offer_ids))
            .group_by(OfferGrant.offer_id)
        )
        return {
            offer_id: GrantStats(offer_id, granted, redeemed) for offer_id, granted, redeemed in rows.tuples()
        }
