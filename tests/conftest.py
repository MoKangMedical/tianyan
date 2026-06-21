import asyncio
from typing import Any

import httpx
import pytest

from demo_server import app


class SyncASGIClient:
    """Small sync wrapper around httpx.ASGITransport for local API tests."""

    def __init__(self, asgi_app):
        self._app = asgi_app

    async def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        transport = httpx.ASGITransport(app=self._app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, url, **kwargs)

    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        return asyncio.run(self._request(method, url, **kwargs))

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", url, **kwargs)


def create_test_client() -> SyncASGIClient:
    return SyncASGIClient(app)


@pytest.fixture(scope="module")
def client():
    """创建测试客户端"""
    return create_test_client()
