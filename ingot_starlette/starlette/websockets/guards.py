"""The guard of the WebSockets: a WebSocket alone, of an origin allowed."""

__all__ = ("StarletteWebSocketOnlyMiddleware", "is_origin_allowed")

import typing as t
import urllib.parse

from starlette.datastructures import Headers
from starlette.exceptions import HTTPException

if t.TYPE_CHECKING:
    from collections.abc import Collection

    from starlette.types import ASGIApp, Receive, Scope, Send


class StarletteWebSocketOnlyMiddleware:
    """
    Refuses a request of HTTP by 426, ``Upgrade: websocket``, and a
    WebSocket of a browser of another origin by 403, against the hijacking
    of a WebSocket by another site (CSWSH): its cookies go with it, whatever
    page opens it. As an ``HTTPException`` its subtree answers.
    """

    def __init__(self, app: "ASGIApp", origins: "Collection[str]" = ()) -> None:
        self._app = app
        self._origins = frozenset(origins)

    async def __call__(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
        # a mount takes no lifespan: a request or a WebSocket
        if scope["type"] == "http":
            raise HTTPException(426, headers={"Upgrade": "websocket"})
        headers = Headers(scope=scope)
        origin = headers.get("origin")
        if not is_origin_allowed(origin, headers.get("host"), self._origins):
            raise HTTPException(403, f"the origin {origin!r} is not allowed")
        await self._app(scope, receive, send)


def is_origin_allowed(
    origin: str | None, host: str | None, origins: "Collection[str]"
) -> bool:
    """
    Whether the ``Origin`` of a WebSocket may open it: none, a client not a
    browser; that of the ``Host`` itself, the same site; or one of
    ``origins``, as ``https://app.example.com``.
    """
    if origin is None:
        return True
    if origin in origins:
        return True
    return host is not None and urllib.parse.urlsplit(origin).netloc == host
