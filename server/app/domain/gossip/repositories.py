from collections.abc import Sequence
from uuid import UUID, uuid4

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert

from app.db.models import GossipGeneration, GossipItem, GossipStatus


class GossipGenerationRepository(SQLAlchemyAsyncRepository[GossipGeneration]):
    model_type = GossipGeneration

    async def create_pending(
        self, point_id: UUID, latitude: float, longitude: float
    ) -> GossipGeneration | None:
        statement = (
            insert(GossipGeneration)
            .values(
                point_id=point_id,
                status=GossipStatus.PENDING,
                attempt_id=uuid4(),
                latitude=latitude,
                longitude=longitude,
            )
            .on_conflict_do_nothing(index_elements=[GossipGeneration.point_id])
            .returning(GossipGeneration.id)
        )
        created_id = (await self.session.execute(statement)).scalar_one_or_none()
        if created_id is None:
            return None
        return await self.get_one(id=created_id)

    async def restart(
        self, generation: GossipGeneration, latitude: float, longitude: float
    ) -> GossipGeneration | None:
        statement = (
            update(GossipGeneration)
            .where(GossipGeneration.id == generation.id, GossipGeneration.attempt_id == generation.attempt_id)
            .values(
                status=GossipStatus.PENDING,
                attempt_id=uuid4(),
                latitude=latitude,
                longitude=longitude,
                error=None,
                finished_at=None,
            )
            .returning(GossipGeneration.id)
        )
        if (await self.session.execute(statement)).scalar_one_or_none() is None:
            return None
        await self.session.refresh(generation)
        return generation


class GossipItemRepository(SQLAlchemyAsyncRepository[GossipItem]):
    model_type = GossipItem

    async def for_point(self, point_id: UUID, include_hidden: bool) -> Sequence[GossipItem]:
        filters = [GossipItem.point_id == point_id]
        if not include_hidden:
            filters.append(GossipItem.is_hidden.is_(False))
        return await self.get_many(*filters, order_by=[(GossipItem.position, False)])

    async def replace_for_point(self, point_id: UUID, items: Sequence[GossipItem]) -> None:
        await self.session.execute(delete(GossipItem).where(GossipItem.point_id == point_id))
        self.session.add_all(items)
        await self.session.flush()
