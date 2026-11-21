"""The WebSockets: the subtree of the connections of a state, at ``/ws``."""

__all__ = (
    "BaseStarletteWebSocketResource",
    "StarletteWebSocketOnlyMiddleware",
    "StarletteWebSocketRoute",
    "StarletteWebSocketsUnit",
)

import typing as t

from ingots.puer import Slot
from starlette.middleware import Middleware

from ..errors import StarletteJsonProblemRenderer
from ..subtrees import BaseStarletteSubtreeUnit
from .guards import StarletteWebSocketOnlyMiddleware
from .resources import BaseStarletteWebSocketResource, StarletteWebSocketRoute

if t.TYPE_CHECKING:
    from collections.abc import Iterator


class StarletteWebSocketsUnit(BaseStarletteSubtreeUnit):
    """
    The subtree of the WebSockets, at ``/ws``: each a resource of a state of
    its own, an entity for each connection, by a factory in a slot of a
    subclass::

        class AppWebSocketsUnit(StarletteWebSocketsUnit):
            chat = Factory(ChatResource)

            @t.override
            def _iter_routes(self):
                yield StarletteWebSocketRoute("/chat/{room}", self.chat)

    A request of HTTP is refused by 426; a WebSocket of a browser of
    another origin than the ``Host`` by 403, unless :meth:`_iter_origins`
    allows it. Its problems are of JSON: a WebSocket refused answers by
    ``application/problem+json``, one accepted gets ``{"problem": ...}`` and
    is closed by ``4000 + status``. Its routes are named under ``ws``.
    """

    renderer = Slot(StarletteJsonProblemRenderer)

    @t.override
    def _get_path(self) -> str:
        return "/ws"

    @t.override
    def _get_name(self) -> str | None:
        return "ws"

    @t.final
    @t.override
    def _iter_guards(self) -> "Iterator[Middleware]":
        origins = tuple(self._iter_origins())
        yield Middleware(StarletteWebSocketOnlyMiddleware, origins=origins)

    def _iter_origins(self) -> "Iterator[str]":
        """
        The origins of the pages of other sites allowed to open a WebSocket,
        as ``https://app.example.com``: none here, the same site alone.
        """
        return iter(())
