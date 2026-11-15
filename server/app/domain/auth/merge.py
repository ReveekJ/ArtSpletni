from collections.abc import Sequence
from typing import Protocol, runtime_checkable
from uuid import UUID

from app.db.models import User
from app.domain.users.services import UserService


@runtime_checkable
class GuestDataMerger(Protocol):
    async def merge_guest(self, guest_id: UUID, target_id: UUID) -> None: ...


class AccountMergeService:
    def __init__(self, users: UserService, mergers: Sequence[GuestDataMerger]) -> None:
        self._users = users
        self._mergers = mergers

    async def absorb_guest(self, guest: User | None, target: User) -> None:
        if guest is None or not guest.is_guest or guest.id == target.id:
            return
        for merger in self._mergers:
            await merger.merge_guest(guest.id, target.id)
        await self._users.delete(guest.id)
