from uuid import UUID

from litestar.background_tasks import BackgroundTask

from app.config import alchemy_config
from app.domain.gossip import deps
from app.domain.gossip.service import GenerationTask


async def run_generation(point_id: UUID, attempt_id: UUID) -> None:
    async with alchemy_config().get_session() as session:
        await deps.build_generation_service(session).generate(point_id, attempt_id)


def background_for(task: GenerationTask | None) -> BackgroundTask | None:
    if task is None:
        return None
    return BackgroundTask(run_generation, task.point_id, task.attempt_id)
