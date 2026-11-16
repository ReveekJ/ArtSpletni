from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import anyio

from app.db.models import BlockKind, MediaKind, OrderingMode, PointKind
from app.domain.demo.catalog import ASSETS_DIR, PARTNERS, OfferSeed, PointSeed, RouteSeed
from app.domain.media.services import MediaService
from app.domain.nfc.services import NfcTagService
from app.domain.offers.schemas import OfferInput
from app.domain.partners.schemas import PartnerInput
from app.domain.partners.services import OfferAdminService, PartnerAdminService, PartnerRepository
from app.domain.points.admin_service import PointAdminService
from app.domain.points.schemas import BlockInput, PointInput
from app.domain.routes.admin_service import RouteAdminService
from app.domain.routes.repositories import RouteRepository
from app.domain.routes.schemas import RouteInput, StopInput

AUDIO_CAPTION = {"ru": "Послушать сплетню", "en": "Listen to the gossip"}


@dataclass(slots=True)
class SeedReport:
    created_routes: list[str] = field(default_factory=list)
    skipped_routes: list[str] = field(default_factory=list)
    scan_urls: list[tuple[str, str]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class DemoSeedServices:
    media: MediaService
    points: PointAdminService
    routes: RouteAdminService
    route_repository: RouteRepository
    partners: PartnerAdminService
    partner_repository: PartnerRepository
    offers: OfferAdminService
    tags: NfcTagService


class DemoContentSeeder:
    def __init__(self, services: DemoSeedServices) -> None:
        self._s = services

    async def seed(self, routes: Sequence[RouteSeed]) -> SeedReport:
        report = SeedReport()
        partner_ids = await self._ensure_partners()
        for route in routes:
            if await self._s.route_repository.get_one_or_none(slug=route.slug) is not None:
                report.skipped_routes.append(route.slug)
                continue
            await self._seed_route(route, partner_ids, report)
            report.created_routes.append(route.slug)
        return report

    async def _ensure_partners(self) -> dict[str, UUID]:
        ids: dict[str, UUID] = {}
        for seed in PARTNERS:
            partner = await self._s.partner_repository.get_one_or_none(name=seed.name)
            if partner is None:
                logo = await self._image(ASSETS_DIR / "logos" / f"{seed.key}.jpg")
                partner = await self._s.partners.create(
                    PartnerInput(name=seed.name, description=seed.description, logo_asset_id=logo)
                )
            ids[seed.key] = partner.id
            existing = {
                offer.title["ru"].text
                for offer in await self._s.offers.list_all(partner.id)
                if "ru" in offer.title
            }
            for offer in seed.offers:
                if offer.title["ru"] not in existing:
                    await self._s.offers.create(self._offer_input(offer, partner.id, None))
        return ids

    async def _seed_route(self, route: RouteSeed, partner_ids: dict[str, UUID], report: SeedReport) -> None:
        point_ids: dict[str, UUID] = {}
        for seed in route.points:
            point_ids[seed.key] = await self._seed_point(seed, partner_ids, report)
        created = await self._s.routes.create(
            RouteInput(
                slug=route.slug,
                title=route.title,
                description={"ru": route.description},
                cover_asset_id=await self._image(ASSETS_DIR / "covers" / f"{route.slug}.jpg"),
                ordering_mode=route.ordering_mode,
                map_visibility=route.map_visibility,
                is_repeatable=route.is_repeatable,
            )
        )
        is_graph = route.ordering_mode is OrderingMode.GRAPH
        stops: dict[UUID, UUID] = {}
        for index, seed in enumerate(route.points):
            updated = await self._s.routes.add_stop(
                created.id,
                StopInput(
                    point_id=point_ids[seed.key],
                    is_start=not seed.depends_on if is_graph else index == 0,
                    is_required=seed.is_required,
                    hint={"ru": seed.hint} if seed.hint else None,
                ),
            )
            stops = {stop.point_id: stop.id for stop in updated.stops}
        if is_graph:
            for seed in route.points:
                for dependency in seed.depends_on:
                    await self._s.routes.add_dependency(
                        created.id, stops[point_ids[seed.key]], stops[point_ids[dependency]]
                    )
        await self._s.routes.set_published(created.id, True)

    async def _seed_point(self, seed: PointSeed, partner_ids: dict[str, UUID], report: SeedReport) -> UUID:
        partner_id = partner_ids[seed.partner] if seed.partner else None
        audio = await self._s.media.store(
            kind=MediaKind.AUDIO,
            content_type="audio/mpeg",
            data=await anyio.Path(ASSETS_DIR / "audio" / f"{seed.key}.mp3").read_bytes(),
            filename=f"{seed.key}.mp3",
            is_public=False,
        )
        point = await self._s.points.create(
            PointInput(
                kind=PointKind.PARTNER if partner_id else PointKind.GOSSIP,
                title=seed.title,
                latitude=seed.latitude,
                longitude=seed.longitude,
                address={"ru": seed.address},
                cover_asset_id=await self._image(ASSETS_DIR / "covers" / f"{seed.key}.jpg"),
                partner_id=partner_id,
                is_published=True,
                blocks=[
                    BlockInput(
                        kind=BlockKind.AUDIO,
                        asset_id=audio.id,
                        caption=AUDIO_CAPTION,
                        transcript={"ru": seed.story},
                    )
                ],
            )
        )
        if seed.offer is not None and partner_id is not None:
            await self._s.offers.create(self._offer_input(seed.offer, partner_id, point.id))
        issued = await self._s.tags.issue(point.id, "demo")
        report.scan_urls.append((seed.title["ru"], issued.url))
        return point.id

    async def _image(self, path: Path) -> UUID:
        asset = await self._s.media.store(
            kind=MediaKind.IMAGE,
            content_type="image/jpeg",
            data=await anyio.Path(path).read_bytes(),
            filename=path.name,
            is_public=True,
        )
        return asset.id

    @staticmethod
    def _offer_input(seed: OfferSeed, partner_id: UUID, point_id: UUID | None) -> OfferInput:
        return OfferInput(
            partner_id=partner_id,
            point_id=point_id,
            title=seed.title,
            terms=seed.terms,
            promo_code=seed.promo_code,
            ttl_hours=seed.ttl_hours,
            redemption_limit=seed.redemption_limit,
            valid_until=datetime.now(UTC) + timedelta(days=seed.valid_days) if seed.valid_days else None,
        )
