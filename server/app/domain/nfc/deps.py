from litestar.di import NamedDependency
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.nfc.services import NfcTagRepository, NfcTagService
from app.lib.settings import get_settings


async def provide_nfc_tag_service(db_session: NamedDependency[AsyncSession]) -> NfcTagService:
    return NfcTagService(NfcTagRepository(session=db_session), get_settings().public_base_url)
