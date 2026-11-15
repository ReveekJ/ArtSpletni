import asyncio

import click

from app.config import alchemy_config
from app.domain.achievements.catalog import STARTER_ACHIEVEMENTS
from app.domain.achievements.deps import build_achievement_admin_service
from app.domain.achievements.schemas import AchievementInput
from app.domain.achievements.services import AchievementRepository
from app.domain.i18n.deps import provide_translation_service
from app.domain.media.services import MediaRepository, MediaService
from app.domain.media.storage import object_storage


async def _seed() -> int:
    created = 0
    async with alchemy_config().get_session() as session:
        service = build_achievement_admin_service(
            session,
            MediaService(MediaRepository(session=session), object_storage()),
            await provide_translation_service(),
        )
        repository = AchievementRepository(session=session)
        for position, seed in enumerate(STARTER_ACHIEVEMENTS):
            if await repository.get_one_or_none(code=seed.code) is not None:
                continue
            await service.create(
                AchievementInput(
                    code=seed.code,
                    title=seed.title,
                    description=seed.description,
                    rule=seed.rule,
                    params=seed.params,
                    is_hidden=seed.is_hidden,
                    position=position,
                )
            )
            created += 1
        await session.commit()
    return created


@click.command(name="seed-achievements", help="Create the starter achievement set (idempotent).")
def seed_achievements_command() -> None:
    click.echo(f"Achievements created: {asyncio.run(_seed())}")
