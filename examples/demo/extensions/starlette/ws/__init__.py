"""
The WebSockets, the subtree at ``/ws``: a resource of a state for each
connection, a new one of its factory each time.
"""

__all__ = ("EchoWebSocketsUnit",)

import typing as t

from ingots.puer import Factory

from ingot_starlette.starlette import StarletteWebSocketsUnit
from ingot_starlette.starlette.websockets import StarletteWebSocketRoute

from .chat import ChatResource
from .stream import StreamResource

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from starlette.routing import BaseRoute


class EchoWebSocketsUnit(StarletteWebSocketsUnit):
    stream = Factory(StreamResource)
    chat = Factory(ChatResource)

    @t.override
    def _iter_routes(self) -> "Iterator[BaseRoute]":
        yield StarletteWebSocketRoute("/stream", self.stream)
        yield StarletteWebSocketRoute("/chat", self.chat)
