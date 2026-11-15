import asyncio

import click

from app.config import alchemy_config
from app.db.models import User, UserKind, UserRole
from app.domain.users.services import UserService, normalize_email
from app.lib.security import hash_password


async def _create_admin(email: str, password: str) -> bool:
    async with alchemy_config().get_session() as session:
        users = UserService(session=session)
        password_hash = await hash_password(password)
        user = await users.get_by_email(email)
        created = user is None
        if user is None:
            user = User(email=normalize_email(email), kind=UserKind.REGISTERED)
        user.password_hash = password_hash
        user.role = UserRole.ADMIN
        user.kind = UserKind.REGISTERED
        await users.upsert(user)
        await session.commit()
    return created


@click.command(name="create-admin", help="Create an administrator or promote an existing account.")
@click.option("--email", required=True, help="Administrator email.")
@click.password_option(help="Administrator password.")
def create_admin_command(email: str, password: str) -> None:
    created = asyncio.run(_create_admin(email, password))
    click.echo(f"Administrator {'created' if created else 'updated'}: {normalize_email(email)}")
