import secrets
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.checkpoint import Checkpoint
from app.repositories.checkpoint_repo import CheckpointRepository
from app.services.storage_service import StorageService


@dataclass(slots=True)
class CheckpointDTO:
    id: int
    slug: str
    title: str
    description: str | None
    latitude: float
    longitude: float
    location_name: str | None
    content_type: str
    text_content: str | None
    image_url: str | None
    loot_type: str | None
    loot_value: str | None
    audio_url: str | None


class CheckpointService:
    def __init__(self, session: AsyncSession, storage: StorageService) -> None:
        self.session = session
        self.repo = CheckpointRepository(session)
        self.storage = storage

    async def get_published_by_slug(self, slug: str) -> CheckpointDTO | None:
        cp = await self.repo.get_by_slug(slug)
        if cp is None or not cp.is_published:
            return None
        return self._to_dto(cp)

    async def get_entity_by_slug(self, slug: str) -> Checkpoint | None:
        return await self.repo.get_by_slug(slug)

    async def list_all(self) -> list[CheckpointDTO]:
        checkpoints = await self.repo.list_all()
        return [self._to_dto(cp) for cp in checkpoints]

    async def create(
        self,
        title: str,
        content_type: str,
        description: str | None,
        latitude: float,
        longitude: float,
        location_name: str | None,
        text_content: str | None,
        image_s3_key: str | None,
        loot_type: str | None,
        loot_value: str | None,
        audio_s3_key: str | None,
        is_published: bool,
    ) -> Checkpoint:
        cp = Checkpoint(
            slug=self.generate_slug(),
            title=title,
            content_type=content_type,
            description=description,
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            text_content=text_content,
            image_s3_key=image_s3_key,
            loot_type=loot_type,
            loot_value=loot_value,
            audio_s3_key=audio_s3_key,
            is_published=is_published,
        )
        return await self.repo.create(cp)

    async def update(self, cp: Checkpoint, **kwargs: object) -> Checkpoint:
        for key, value in kwargs.items():
            if hasattr(cp, key) and value is not None:
                setattr(cp, key, value)
        return await self.repo.update(cp)

    async def delete(self, cp: Checkpoint) -> None:
        if cp.image_s3_key:
            self.storage.delete(cp.image_s3_key)
        if cp.audio_s3_key:
            self.storage.delete(cp.audio_s3_key)
        await self.repo.delete(cp)

    def _to_dto(self, cp: Checkpoint) -> CheckpointDTO:
        return CheckpointDTO(
            id=cp.id,
            slug=cp.slug,
            title=cp.title,
            description=cp.description,
            latitude=cp.latitude,
            longitude=cp.longitude,
            location_name=cp.location_name,
            content_type=cp.content_type,
            text_content=cp.text_content,
            image_url=(
                self.storage.presign_get(cp.image_s3_key, 3600)
                if cp.image_s3_key
                else None
            ),
            loot_type=cp.loot_type,
            loot_value=cp.loot_value,
            audio_url=(
                self.storage.presign_get(cp.audio_s3_key, 3600)
                if cp.audio_s3_key
                else None
            ),
        )

    @staticmethod
    def generate_slug() -> str:
        return secrets.token_urlsafe(8)
