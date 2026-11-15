import base64
import hashlib
from urllib.parse import urlencode

import httpx
import msgspec

from app.lib.exceptions import BadRequestError
from app.lib.settings import YandexSettings

AUTHORIZE_URL = "https://oauth.yandex.ru/authorize"
TOKEN_URL = "https://oauth.yandex.ru/token"
PROFILE_URL = "https://login.yandex.ru/info"


class YandexToken(msgspec.Struct):
    access_token: str


class YandexProfile(msgspec.Struct):
    id: str
    default_email: str | None = None
    display_name: str | None = None
    real_name: str | None = None


def code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


class YandexOAuthClient:
    def __init__(self, settings: YandexSettings, http: httpx.AsyncClient) -> None:
        self._settings = settings
        self._http = http

    def authorize_url(self, state: str, verifier: str) -> str:
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self._settings.client_id,
                "redirect_uri": self._settings.redirect_uri,
                "state": state,
                "code_challenge": code_challenge(verifier),
                "code_challenge_method": "S256",
            }
        )
        return f"{AUTHORIZE_URL}?{query}"

    async def fetch_profile(self, code: str, verifier: str) -> YandexProfile:
        try:
            return await self._fetch_profile(code, verifier)
        except (httpx.HTTPError, msgspec.DecodeError, msgspec.ValidationError) as exc:
            raise BadRequestError("Yandex ID request failed", code="oauth_failed") from exc

    async def _fetch_profile(self, code: str, verifier: str) -> YandexProfile:
        token_response = await self._http.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self._settings.client_id,
                "client_secret": self._settings.client_secret.get_secret_value(),
                "code_verifier": verifier,
            },
        )
        if token_response.status_code != httpx.codes.OK:
            raise BadRequestError("Yandex rejected the authorization code", code="oauth_failed")
        token = msgspec.json.decode(token_response.content, type=YandexToken)
        profile_response = await self._http.get(
            PROFILE_URL,
            params={"format": "json"},
            headers={"Authorization": f"OAuth {token.access_token}"},
        )
        profile_response.raise_for_status()
        return msgspec.json.decode(profile_response.content, type=YandexProfile)
