import asyncio

import click
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import alchemy_config
from app.domain.demo.ekb import EKB_ROUTES
from app.domain.demo.msk import MSK_ROUTES
from app.domain.demo.seeder import DemoContentSeeder, DemoSeedServices, SeedReport
from app.domain.i18n.deps import provide_translation_service
from app.domain.media.deps import provide_media_service
from app.domain.nfc.deps import provide_nfc_tag_service
from app.domain.offers.deps import (
    provide_offer_admin_service,
    provide_partner_admin_service,
    provide_partner_repository,
)
from app.domain.points.deps import provide_point_admin_service
from app.domain.routes.deps import provide_route_admin_service
from app.domain.routes.repositories import RouteRepository


async def build_demo_seed_services(session: AsyncSession) -> DemoSeedServices:
    media = await provide_media_service(session)
    translator = await provide_translation_service()
    return DemoSeedServices(
        media=media,
        points=await provide_point_admin_service(session, media, translator),
        routes=await provide_route_admin_service(session, media, translator),
        route_repository=RouteRepository(session=session),
        partners=await provide_partner_admin_service(session, media, translator),
        partner_repository=await provide_partner_repository(session),
        offers=await provide_offer_admin_service(session, translator),
        tags=await provide_nfc_tag_service(session),
    )


async def _seed_demo_content() -> SeedReport:
    async with alchemy_config().get_session() as session:
        seeder = DemoContentSeeder(await build_demo_seed_services(session))
        report = await seeder.seed((*EKB_ROUTES, *MSK_ROUTES))
        await session.commit()
    return report


@click.command(
    name="seed-demo-content",
    help="Create demo routes, points, partners and offers in Yekaterinburg and Moscow (idempotent by route slug).",
)
def seed_demo_content_command() -> None:
    report = asyncio.run(_seed_demo_content())
    click.echo(f"Routes created: {', '.join(report.created_routes) or '-'}")
    click.echo(f"Routes skipped (already exist): {', '.join(report.skipped_routes) or '-'}")
    for title, url in report.scan_urls:
        click.echo(f"  {title}: {url}")
