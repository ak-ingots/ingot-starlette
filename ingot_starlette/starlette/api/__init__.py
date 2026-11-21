"""The API: the subtree of JSON, and of JSON alone."""

__all__ = ("StarletteApiUnit", "StarletteJsonOnlyMiddleware")

import typing as t

from ingots.puer import Slot
from starlette.middleware import Middleware

from ..errors import StarletteJsonProblemRenderer
from ..subtrees import BaseStarletteSubtreeUnit

from .guards import StarletteJsonOnlyMiddleware

if t.TYPE_CHECKING:
    from collections.abc import Iterator


class StarletteApiUnit(BaseStarletteSubtreeUnit):
    """
    The subtree of the API, at ``/api``: for the clients of a script, a
    single page, a phone. It takes and gives JSON alone: a request whose
    ``Accept`` takes no JSON is refused by 406, a body not of JSON by 415; its
    errors are problems of ``application/problem+json``, its not found and
    its faults too. Its endpoints, and its nodes, in the slots of a
    subclass::

        class AppApiUnit(StarletteApiUnit):
            echo = Slot(EchoEndpoint)

            @t.override
            def _iter_routes(self):
                yield from self.echo.get_routes()

    Its routes are named under ``api``: ``url_path_for("api:send")``.
    """

    renderer = Slot(StarletteJsonProblemRenderer)

    @t.override
    def _get_path(self) -> str:
        return "/api"

    @t.override
    def _get_name(self) -> str | None:
        return "api"

    @t.final
    @t.override
    def _iter_guards(self) -> "Iterator[Middleware]":
        yield Middleware(StarletteJsonOnlyMiddleware)
