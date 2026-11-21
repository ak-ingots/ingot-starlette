"""
Starlette in the application, the root of the tree of the routes: the API
mounted at ``/api``, the policies of the errors, the middleware.
"""

__all__ = ("EchoStarletteUnit",)

import typing as t

from ingots.puer import Slot
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount

from ingot_starlette.starlette import StarletteUnit

from .api import ApiEndpoint
from .errors import EchoStarletteErrorsUnit

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from starlette.routing import BaseRoute


class EchoStarletteUnit(StarletteUnit):
    errors = Slot(EchoStarletteErrorsUnit)
    api = Slot(ApiEndpoint)

    @t.override
    def _iter_routes(self) -> "Iterator[BaseRoute]":
        yield Mount("/api", routes=self.api.get_routes(), name="api")

    @t.override
    def _iter_middleware(self) -> "Iterator[Middleware]":
        yield Middleware(CORSMiddleware, allow_origins=["https://echo.example.com"])
