"""
The API, the subtree of JSON at ``/api``: an endpoint for each resource in
its slots, their routes its own; its middleware, CORS for the pages of
another origin. A package for each node, a module for each leaf: the tree
of the packages is that of the paths.
"""

__all__ = ("EchoApiUnit",)

import typing as t

from ingots.puer import Slot
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from ingot_starlette.starlette import StarletteApiUnit

from .echo import EchoEndpoint
from .ticks import TicksEndpoint

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from starlette.routing import BaseRoute


class EchoApiUnit(StarletteApiUnit):
    echo = Slot(EchoEndpoint)
    ticks = Slot(TicksEndpoint)

    @t.override
    def _iter_routes(self) -> "Iterator[BaseRoute]":
        yield from self.echo.get_routes()
        yield from self.ticks.get_routes()

    @t.override
    def _iter_middleware(self) -> "Iterator[Middleware]":
        yield Middleware(CORSMiddleware, allow_origins=["https://echo.example.com"])
