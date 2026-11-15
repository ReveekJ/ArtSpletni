from collections.abc import Sequence

from litestar.di import NamedDependency
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.achievements.deps import build_achievement_service
from app.domain.media.services import MediaService
from app.domain.nfc.services import NfcTagRepository, NfcTagService
from app.domain.offers.deps import build_offer_service
from app.domain.offers.listener import OfferProgressListener
from app.domain.points.repositories import PointRepository, UnlockRepository
from app.domain.routes.repositories import RouteRepository
from app.domain.runs.catalog import RouteCatalogService
from app.domain.runs.events import ProgressEventBus, ProgressListener
from app.domain.runs.repositories import RunRepository
from app.domain.runs.schemas import RunPresenter
from app.domain.runs.services import RunService
from app.domain.scans.services import ScanEventRepository, ScanService
from app.domain.users.services import UserService
from app.lib.settings import get_settings


async def provide_progress_listeners(
    db_session: NamedDependency[AsyncSession], language: NamedDependency[str]
) -> Sequence[ProgressListener]:
    fallback = get_settings().default_language
    return (
        OfferProgressListener(build_offer_service(db_session), language, fallback),
        build_achievement_service(db_session, language),
    )


async def provide_progress_bus(
    progress_listeners: NamedDependency[Sequence[ProgressListener]],
) -> ProgressEventBus:
    return ProgressEventBus(progress_listeners)


async def provide_run_presenter(language: NamedDependency[str]) -> RunPresenter:
    return RunPresenter(language, get_settings().default_language)


async def provide_run_service(db_session: NamedDependency[AsyncSession]) -> RunService:
    return RunService(RunRepository(session=db_session), UnlockRepository(session=db_session))


async def provide_scan_service(
    db_session: NamedDependency[AsyncSession],
    run_service: NamedDependency[RunService],
    progress_bus: NamedDependency[ProgressEventBus],
) -> ScanService:
    return ScanService(
        tags=NfcTagService(NfcTagRepository(session=db_session), get_settings().public_base_url),
        users=UserService(session=db_session),
        points=PointRepository(session=db_session),
        unlocks=UnlockRepository(session=db_session),
        routes=RouteRepository(session=db_session),
        runs=run_service,
        scan_events=ScanEventRepository(session=db_session),
        bus=progress_bus,
    )


async def provide_route_catalog_service(
    db_session: NamedDependency[AsyncSession],
    media_service: NamedDependency[MediaService],
    run_presenter: NamedDependency[RunPresenter],
) -> RouteCatalogService:
    return RouteCatalogService(
        RouteRepository(session=db_session),
        PointRepository(session=db_session),
        RunRepository(session=db_session),
        media_service,
        run_presenter,
    )
