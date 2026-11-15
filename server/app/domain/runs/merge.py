from uuid import UUID

from app.domain.runs.repositories import GuestProgressRepository


class GuestProgressMerger:
    def __init__(self, repository: GuestProgressRepository) -> None:
        self._repository = repository

    async def merge_guest(self, guest_id: UUID, target_id: UUID) -> None:
        await self._repository.move_unlocks(guest_id, target_id)
        await self._repository.move_runs(guest_id, target_id)
