from __future__ import annotations

import jwt
import pytest
from starlette.requests import Request

from src.web.middleware.middleware import LoggingMiddleware, LoggingMiddlewareOld

pytestmark = pytest.mark.unit


def _request(headers: list[tuple[bytes, bytes]] | None = None) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/health",
            "raw_path": b"/health",
            "query_string": b"",
            "headers": headers or [],
            "client": ("127.0.0.1", 12345),
            "server": ("test", 80),
            "scheme": "http",
            "http_version": "1.1",
        }
    )


@pytest.mark.parametrize("middleware_cls", [LoggingMiddleware, LoggingMiddlewareOld])
def test_extract_bearer_token(middleware_cls) -> None:
    request = _request([(b"authorization", b"Bearer abc.def")])
    assert middleware_cls._extract_bearer_token(request) == "abc.def"
    assert middleware_cls._extract_bearer_token(_request()) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("middleware_cls", [LoggingMiddleware, LoggingMiddlewareOld])
async def test_get_username_from_token_without_signature_validation(middleware_cls) -> None:
    token = jwt.encode({"sub": "alice"}, "unused", algorithm="HS256")
    assert await middleware_cls._get_username_from_token(token) == "alice"
    assert await middleware_cls._get_username_from_token("not-a-jwt") == "invalid_token"
