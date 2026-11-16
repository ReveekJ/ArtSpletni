import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MediaAsset, MediaStatus, NfcTag, Offer, Route
from app.domain.demo.cli import _seed_demo_content
from tests.fakes import FakeObjectStorage, FakeTranslationProvider

pytestmark = pytest.mark.routes


async def test_seed_demo_content_creates_published_routes(
    db_session: AsyncSession, storage: FakeObjectStorage, translator: FakeTranslationProvider
) -> None:
    report = await _seed_demo_content()
    assert len(report.created_routes) == 4
    assert len(report.scan_urls) == 18

    routes = (await db_session.scalars(select(Route))).all()
    assert all(route.is_published for route in routes)
    assert await db_session.scalar(select(func.count()).select_from(Offer)) == 6
    assert await db_session.scalar(select(func.count()).select_from(NfcTag)) == 18
    assets = (await db_session.scalars(select(MediaAsset))).all()
    assert all(asset.status is MediaStatus.READY for asset in assets)
    assert {asset.storage_key for asset in assets} == set(storage.objects)

    again = await _seed_demo_content()
    assert again.created_routes == []
    assert len(again.skipped_routes) == 4
    assert await db_session.scalar(select(func.count()).select_from(Offer)) == 6
