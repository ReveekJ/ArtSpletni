from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.checkpoint import Checkpoint


class CheckpointRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_slug(self, slug: str) -> Checkpoint | None:
        stmt = select(Checkpoint).where(Checkpoint.slug == slug)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, checkpoint_id: int) -> Checkpoint | None:
        return await self.session.get(Checkpoint, checkpoint_id)

    async def list_all(self) -> list[Checkpoint]:
        stmt = select(Checkpoint).order_by(Checkpoint.id.desc())
        return list((await self.session.execute(stmt)).scalars().all())

    async def create(self, checkpoint: Checkpoint) -> Checkpoint:
        self.session.add(checkpoint)
        await self.session.commit()
        await self.session.refresh(checkpoint)
        return checkpoint

    async def update(self, checkpoint: Checkpoint) -> Checkpoint:
        await self.session.commit()
        await self.session.refresh(checkpoint)
        return checkpoint

    async def delete(self, checkpoint: Checkpoint) -> None:
        await self.session.delete(checkpoint)
        await self.session.commit()
