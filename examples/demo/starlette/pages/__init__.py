"""The pages, the subtree of HTML: every path the API does not take."""

__all__ = ("EchoPagesUnit",)

import typing as t

from ingots.puer import Slot

from ingot_starlette.starlette import StarlettePagesUnit

from .home import HomePage
from .socket import SocketPage

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from starlette.routing import BaseRoute


class EchoPagesUnit(StarlettePagesUnit):
    home = Slot(HomePage)
    socket = Slot(SocketPage)

    @t.override
    def _iter_routes(self) -> "Iterator[BaseRoute]":
        yield from self.home.get_routes()
        yield from self.socket.get_routes()
