from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from litestar import Litestar
from litestar.datastructures import State

HTTP_CLIENT_STATE_KEY = "http_client"


@asynccontextmanager
async def http_client_lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        app.state[HTTP_CLIENT_STATE_KEY] = client
        yield


def provide_http_client(state: State) -> httpx.AsyncClient:
    client = state.get(HTTP_CLIENT_STATE_KEY)
    if not isinstance(client, httpx.AsyncClient):
        raise RuntimeError("HTTP client is not initialised")
    return client
