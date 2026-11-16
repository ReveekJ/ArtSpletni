import asyncio

import click

from app.config import alchemy_config
from app.db.models import Partner, PartnerMember, User, UserKind
from app.domain.auth.demo import DEMO_ACCOUNTS, DEMO_PARTNER_NAME
from app.domain.partners.services import PartnerMemberRepository, PartnerRepository
from app.domain.users.services import UserService
from app.lib.security import hash_password


async def _seed_demo_users(password: str | None) -> int:
    async with alchemy_config().get_session() as session:
        users = UserService(session=session)
        partners = PartnerRepository(session=session)
        members = PartnerMemberRepository(session=session)
        password_hash = await hash_password(password) if password else None
        for account in DEMO_ACCOUNTS:
            user = await users.get_by_email(account.email) or User(email=account.email)
            user.display_name = account.display_name
            user.kind = UserKind.REGISTERED
            user.role = account.role
            user.is_active = True
            if password_hash is not None:
                user.password_hash = password_hash
            user = await users.upsert(user)
            if account.is_partner:
                partner = await partners.get_one_or_none(name=DEMO_PARTNER_NAME) or await partners.add(
                    Partner(name=DEMO_PARTNER_NAME)
                )
                if await members.get_one_or_none(partner_id=partner.id, user_id=user.id) is None:
                    await members.add(PartnerMember(partner_id=partner.id, user_id=user.id))
        await session.commit()
    return len(DEMO_ACCOUNTS)


@click.command(name="seed-demo-users", help="Create or refresh demo accounts for quick login (idempotent).")
@click.option(
    "--password",
    default=None,
    help="Optional shared password for email login; without it demo accounts are reachable only via quick login.",
)
def seed_demo_users_command(password: str | None) -> None:
    click.echo(f"Demo accounts seeded: {asyncio.run(_seed_demo_users(password))}")
