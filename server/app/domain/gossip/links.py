import asyncio
import ipaddress
import logging
import socket
from urllib.parse import urlsplit

import httpx

logger = logging.getLogger(__name__)

ALLOWED_SCHEMES: frozenset[str] = frozenset({"http", "https"})
HEAD_UNSUPPORTED_STATUSES: frozenset[int] = frozenset({403, 405, 501})


class LinkValidator:
    def __init__(self, user_agent: str, timeout_seconds: float) -> None:
        self._headers = {"User-Agent": user_agent}
        self._timeout = timeout_seconds

    async def filter_alive(self, urls: list[str]) -> set[str]:
        unique = list(dict.fromkeys(urls))
        if not unique:
            return set()
        async with httpx.AsyncClient(
            headers=self._headers, timeout=self._timeout, follow_redirects=False
        ) as client:
            results = await asyncio.gather(*(self._is_alive(client, url) for url in unique))
        return {url for url, alive in zip(unique, results, strict=True) if alive}

    async def _is_alive(self, client: httpx.AsyncClient, url: str) -> bool:
        if not await self._is_public_url(url):
            logger.info("Rejected non-public gossip link: %s", url)
            return False
        try:
            response = await client.head(url)
            if response.status_code not in HEAD_UNSUPPORTED_STATUSES:
                return response.status_code < 400
            async with client.stream("GET", url) as streamed:
                return streamed.status_code < 400
        except httpx.HTTPError as exc:
            logger.info("Gossip link check failed for %s: %s", url, exc)
            return False

    @staticmethod
    async def _is_public_url(url: str) -> bool:
        try:
            parts = urlsplit(url)
            port = parts.port or (443 if parts.scheme == "https" else 80)
        except ValueError:
            return False
        if parts.scheme not in ALLOWED_SCHEMES or not parts.hostname:
            return False
        try:
            infos = await asyncio.get_running_loop().getaddrinfo(
                parts.hostname, port, type=socket.SOCK_STREAM
            )
        except OSError as exc:
            logger.info("Gossip link host does not resolve %s: %s", url, exc)
            return False
        addresses = {str(info[4][0]) for info in infos}
        return bool(addresses) and all(
            ipaddress.ip_address(address.split("%", 1)[0]).is_global for address in addresses
        )
