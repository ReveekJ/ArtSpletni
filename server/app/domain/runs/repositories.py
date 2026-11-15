from collections.abc import Sequence
from uuid import UUID

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import func, select, update

from app.db.models import RouteRun, RunStatus, ScanEvent, Unlock


class RunRepository(SQLAlchemyAsyncRepository[RouteRun]):
    model_type = RouteRun

    async def active_for_user(self, user_id: UUID) -> RouteRun | None:
        return await self.get_one_or_none(user_id=user_id, status=RunStatus.ACTIVE)

    async def for_user(self, user_id: UUID) -> Sequence[RouteRun]:
        return await self.get_many(RouteRun.user_id == user_id, order_by=[(RouteRun.updated_at, True)])

    async def for_user_route(self, user_id: UUID, route_id: UUID) -> Sequence[RouteRun]:
        return await self.get_many(
            RouteRun.user_id == user_id,
            RouteRun.route_id == route_id,
            order_by=[(RouteRun.created_at, True)],
        )

    async def completed_count(self, route_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(RouteRun)
            .where(RouteRun.route_id == route_id, RouteRun.status == RunStatus.COMPLETED)
        )
        return int(result.scalar_one())


class GuestProgressRepository:
    def __init__(self, runs: RunRepository) -> None:
        self._session = runs.session

    async def move_unlocks(self, guest_id: UUID, target_id: UUID) -> None:
        guest_unlocks = (await self._session.scalars(select(Unlock).where(Unlock.user_id == guest_id))).all()
        target_unlocks = {
            unlock.point_id: unlock
            for unlock in (
                await self._session.scalars(select(Unlock).where(Unlock.user_id == target_id))
            ).all()
        }
        for unlock in guest_unlocks:
            existing = target_unlocks.get(unlock.point_id)
            if existing is None:
                unlock.user_id = target_id
                continue
            if unlock.created_at < existing.created_at:
                existing.created_at = unlock.created_at
            await self._session.delete(unlock)
        await self._session.flush()

    async def move_runs(self, guest_id: UUID, target_id: UUID) -> None:
        active = (
            await self._session.scalars(
                select(RouteRun).where(
                    RouteRun.user_id.in_([guest_id, target_id]), RouteRun.status == RunStatus.ACTIVE
                )
            )
        ).all()
        if len(active) > 1:
            for run in sorted(active, key=lambda item: item.updated_at)[:-1]:
                run.status = RunStatus.PAUSED
            await self._session.flush()
        await self._session.execute(
            update(RouteRun).where(RouteRun.user_id == guest_id).values(user_id=target_id)
        )
        await self._session.execute(
            update(ScanEvent).where(ScanEvent.user_id == guest_id).values(user_id=target_id)
        )
