"""
The Starlette unit: the application of the project, its three subtrees,
the API, the WebSockets and the pages, its callers and errors.
"""

__all__ = (
    "BaseStarletteSubtreeUnit",
    "StarletteApiUnit",
    "StarletteCallers",
    "StarletteEndpoint",
    "StarlettePagesUnit",
    "StarletteUnit",
    "StarletteWebSocketsUnit",
)

import typing as t

from ingots.puer import Slot, Unit

from .callers import StarletteCallers
from .endpoints import StarletteEndpoint
from .errors import StarletteErrorsUnit
from .subtrees import BaseStarletteSubtreeUnit
from .api import StarletteApiUnit
from .pages import StarlettePagesUnit
from .websockets import StarletteWebSocketsUnit

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from ingots.defaults.operations import BaseOperation
    from ingots.puer import BoundFactory
    from starlette.middleware import Middleware
    from starlette.requests import HTTPConnection
    from starlette.routing import BaseRoute

    from ingot_starlette.project import StarletteProject


class StarletteUnit(StarletteEndpoint, Unit):
    """
    Starlette in the project, the root endpoint: what the application of
    :class:`~ingot_starlette.runner.StarletteRunner` takes once the project is
    configured. Its routes are its three subtrees, each a mount of its own
    middleware and errors: :attr:`api`, of JSON alone, at ``/api``;
    :attr:`ws`, of the WebSockets, a resource of a state for each
    connection, at ``/ws``; and :attr:`pages`, of HTML, every other path. An
    application fills them in subclasses, and adds the middleware of the
    whole application by :meth:`_iter_middleware`, of Starlette as they are::

        class AppStarletteUnit(StarletteUnit):
            errors = Slot(AppStarletteErrorsUnit)
            api = Slot(AppApiUnit)
            ws = Slot(AppWebSocketsUnit)
            pages = Slot(AppPagesUnit)

            @t.override
            def _iter_middleware(self):
                yield Middleware(GZipMiddleware)

    The operations of a request run for the caller :attr:`callers` tells, by
    :meth:`run_operation`; the exceptions answer by the policies of
    :attr:`errors`, in the form of their subtree.
    """

    project: "StarletteProject"

    callers = Slot(StarletteCallers)
    errors = Slot(StarletteErrorsUnit)
    api = Slot(StarletteApiUnit)
    ws = Slot(StarletteWebSocketsUnit)
    pages = Slot(StarlettePagesUnit)

    @t.final
    def get_middleware(self) -> "list[Middleware]":
        """The middleware of the application, the outermost first."""
        return list(self._iter_middleware())

    @t.final
    async def run_operation[ParametersType, ResultType](
        self,
        factory: "BoundFactory[BaseOperation[ParametersType, ResultType]]",
        parameters: ParametersType,
        connection: "HTTPConnection",
    ) -> ResultType:
        """Runs an operation for the caller of a request or a WebSocket."""
        operations = self.project.operations
        metadata = operations.create_metadata(await self.callers.get(connection))
        return await operations.runner.run(factory, parameters, metadata)

    @t.final
    @t.override
    def _iter_routes(self) -> "Iterator[BaseRoute]":
        yield self.api.get_mount()
        yield self.ws.get_mount()
        yield self.pages.get_mount()

    def _iter_middleware(self) -> "Iterator[Middleware]":
        """
        The middleware of the whole application, the outermost first, outside
        those of the subtrees: none here. A subclass adding to
        those of its base yields them too.
        """
        return iter(())
