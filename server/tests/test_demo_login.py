import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PartnerMember, User
from app.domain.auth.cli import _seed_demo_users
from app.lib.settings import get_settings
from tests.conftest import Client

pytestmark = pytest.mark.auth


@pytest.fixture
def demo_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "demo_login_enabled", True)


async def test_options_hide_demo_accounts_when_disabled(client: Client) -> None:
    await _seed_demo_users(None)
    options = (await client.get("/api/auth/options")).json()
    assert options == {"yandexEnabled": True, "demoAccounts": []}

    response = await client.post("/api/auth/demo/admin")
    assert response.status_code == 404
    assert response.json()["code"] == "demo_login_disabled"


async def test_options_list_only_seeded_accounts(client: Client, demo_enabled: None) -> None:
    assert (await client.get("/api/auth/options")).json()["demoAccounts"] == []

    await _seed_demo_users(None)
    keys = [item["key"] for item in (await client.get("/api/auth/options")).json()["demoAccounts"]]
    assert keys == ["admin", "partner", "anna", "boris", "tourist"]


async def test_demo_login_binds_session(client: Client, demo_enabled: None) -> None:
    await _seed_demo_users(None)
    profile = (await client.post("/api/auth/demo/admin")).json()
    assert profile["role"] == "admin"
    assert (await client.get("/api/auth/session")).json()["user"]["id"] == profile["id"]
    assert (await client.get("/api/admin/points")).status_code == 200

    unknown = await client.post("/api/auth/demo/nobody")
    assert unknown.status_code == 404
    assert unknown.json()["code"] == "demo_account_not_found"


async def test_seed_is_idempotent_and_links_partner(db_session: AsyncSession) -> None:
    await _seed_demo_users(None)
    await _seed_demo_users("demo-password-1")
    partner_user = await db_session.scalar(select(User).where(User.email == "partner@demo.spletni.local"))
    assert partner_user is not None
    assert partner_user.password_hash is not None
    members = await db_session.scalars(select(PartnerMember).where(PartnerMember.user_id == partner_user.id))
    assert len(members.all()) == 1
