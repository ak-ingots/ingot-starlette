"""
The API, a node of the tree of the routes: an endpoint and a unit, holding
the endpoints of its resources in its slots and mounting their routes, as
the Starlette unit mounts it. A package for each node, a module for each
leaf: the tree of the packages is that of the paths.
"""

__all__ = ("ApiEndpoint",)

import typing as t

from ingots.puer import Slot, Unit

from ingot_starlette.starlette import StarletteEndpoint

from .echo import EchoEndpoint
from .stream import StreamEndpoint
from .ticks import TicksEndpoint

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from starlette.routing import BaseRoute


class ApiEndpoint(StarletteEndpoint, Unit):
    echo = Slot(EchoEndpoint)
    ticks = Slot(TicksEndpoint)
    stream = Slot(StreamEndpoint)

    @t.override
    def _iter_routes(self) -> "Iterator[BaseRoute]":
        yield from self.echo.get_routes()
        yield from self.ticks.get_routes()
        yield from self.stream.get_routes()
