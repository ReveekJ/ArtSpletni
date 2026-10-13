from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.route_stop import RouteStop
from app.entities.user import User
from app.repositories.progress_repo import ProgressRepository
from app.repositories.route_stop_repo import RouteStopRepository


@dataclass(slots=True)
class StopStatusDTO:
    stop_id: int
    is_unlocked: bool
    is_completed: bool


@dataclass(slots=True)
class RouteProgressDTO:
    route_id: int
    total_stops: int
    completed_stops: int
    stop_statuses: list[StopStatusDTO]


class ProgressService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.progress_repo = ProgressRepository(session)
        self.stop_repo = RouteStopRepository(session)

    async def is_stop_unlocked(self, stop: RouteStop, user: User | None) -> bool:
        if user is None:
            return False
        deps = await self.stop_repo.get_dependencies(stop.id)
        if not deps:
            return True
        completed = await self.progress_repo.get_completed_stop_ids(user.id)
        return all(dep.depends_on_stop_id in completed for dep in deps)

    async def record_completion(
        self, user: User, stop: RouteStop,
    ) -> None:
        await self.progress_repo.record_completion(user.id, stop.id)

    async def get_route_progress(
        self, route_id: int, user: User | None,
    ) -> RouteProgressDTO:
        stops = await self.stop_repo.list_by_route(route_id)
        if user is None:
            return RouteProgressDTO(
                route_id=route_id,
                total_stops=len(stops),
                completed_stops=0,
                stop_statuses=[
                    StopStatusDTO(
                        stop_id=s.id,
                        is_unlocked=not await self.stop_repo.get_dependencies(s.id),
                        is_completed=False,
                    )
                    for s in stops
                ],
            )
        completed = await self.progress_repo.get_completed_stop_ids(user.id)
        statuses: list[StopStatusDTO] = []
        for stop in stops:
            deps = await self.stop_repo.get_dependencies(stop.id)
            is_unlocked = all(dep.depends_on_stop_id in completed for dep in deps)
            statuses.append(
                StopStatusDTO(
                    stop_id=stop.id,
                    is_unlocked=is_unlocked,
                    is_completed=stop.id in completed,
                )
            )
        return RouteProgressDTO(
            route_id=route_id,
            total_stops=len(stops),
            completed_stops=sum(1 for s in statuses if s.is_completed),
            stop_statuses=statuses,
        )

    async def check_and_record_listen_progress(
        self,
        user: User,
        track_id: int,
        completion_ratio: float | None,
        is_completed: bool,
    ) -> None:
        from app.services.route_service import RouteService
        from app.services.storage_service import get_storage

        route_service = RouteService(self.session, get_storage())
        stops = await route_service.find_stops_for_track(track_id)
        for stop in stops:
            if stop.stop_type != "track":
                continue
            criteria = stop.completion_criteria
            should_record = False
            if criteria == "scan" or criteria == "listen_any":
                should_record = True
            elif criteria == "listen_95":
                should_record = (
                    completion_ratio is not None and completion_ratio >= 0.95
                ) or is_completed
            elif criteria == "listen_100":
                should_record = (
                    completion_ratio is not None and completion_ratio >= 1.0
                ) or is_completed
            if should_record:
                await self.progress_repo.record_completion(user.id, stop.id)
