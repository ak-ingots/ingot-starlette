"""The guard of the API: JSON, and JSON alone, both ways."""

__all__ = ("StarletteJsonOnlyMiddleware", "accepts_json", "is_json")

import typing as t

from starlette.datastructures import Headers
from starlette.exceptions import HTTPException

if t.TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send

_JSON_TYPES: t.Final = ("application/json", "application/problem+json")


class StarletteJsonOnlyMiddleware:
    """
    Refuses a request of HTTP not of JSON: an ``Accept`` that takes no JSON
    by 406, a body not of JSON, by its ``Content-Type``, by 415; a WebSocket
    by 404, its place the subtree of the WebSockets. As an ``HTTPException``
    its subtree answers.
    """

    def __init__(self, app: "ASGIApp") -> None:
        self._app = app

    async def __call__(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
        # a mount takes no lifespan: a request or a WebSocket
        if scope["type"] == "websocket":
            raise HTTPException(404, "a WebSocket is not of the API")
        headers = Headers(scope=scope)
        if not accepts_json(headers.get("accept")):
            raise HTTPException(406)
        has_body = int(headers.get("content-length", "0") or "0") > 0
        has_body = has_body or "transfer-encoding" in headers
        if has_body and not is_json(headers.get("content-type", "")):
            raise HTTPException(415)
        await self._app(scope, receive, send)


def accepts_json(accept: str | None) -> bool:
    """
    Whether an ``Accept`` takes JSON, or a problem of JSON: none takes all;
    the quality of a type that of its most specific range, ``q=0`` a refusal.
    """
    if not accept:
        return True
    ranges: list[tuple[str, float]] = []
    for part in accept.split(","):
        media, *params = (item.strip() for item in part.split(";"))
        quality = 1.0
        for param in params:
            key, _, value = param.partition("=")
            if key.strip().lower() == "q":
                try:
                    quality = float(value)
                except ValueError:
                    quality = 0.0
        ranges.append((media.lower(), quality))
    return any(_get_quality(ranges, media) > 0 for media in _JSON_TYPES)


def is_json(content_type: str) -> bool:
    """Whether a ``Content-Type`` is of JSON: ``application/json``, ``*+json``."""
    media = content_type.split(";")[0].strip().lower()
    return media == "application/json" or (
        media.startswith("application/") and media.endswith("+json")
    )


def _get_quality(ranges: list[tuple[str, float]], media: str) -> float:
    family = media.partition("/")[0] + "/*"
    best: tuple[int, float] | None = None  # the specificity, the quality
    for value, quality in ranges:
        specificity = {media: 2, family: 1, "*/*": 0}.get(value)
        if specificity is not None and (best is None or specificity > best[0]):
            best = (specificity, quality)
    return best[1] if best else 0.0
