"""The Starlette unit: the application of the project, its callers and errors."""

__all__ = ("StarletteCallers", "StarletteEndpoint", "StarletteUnit")

import typing as t

from ingots.puer import Slot, Unit

from .callers import StarletteCallers
from .endpoints import StarletteEndpoint
from .errors import StarletteErrorsUnit

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from ingots.defaults.operations import BaseOperation
    from ingots.puer import BoundFactory
    from starlette.middleware import Middleware
    from starlette.requests import HTTPConnection

    from ingot_starlette.project import StarletteProject


class StarletteUnit(StarletteEndpoint, Unit):
    """
    Starlette in the project, the root endpoint: what the application of
    :class:`~ingot_starlette.runner.StarletteRunner` takes once the project is
    configured, the routes of :meth:`_iter_routes`, those of the endpoints of
    the slots of a subclass mounted where it puts them, and the middleware of
    :meth:`_iter_middleware`, of Starlette as they are::

        class AppStarletteUnit(StarletteUnit):
            api = Slot(ApiEndpoint)  # an endpoint and a unit, of endpoints

            @t.override
            def _iter_routes(self):
                yield Mount("/api", routes=self.api.get_routes(), name="api")

            @t.override
            def _iter_middleware(self):
                yield Middleware(GZipMiddleware)

    The operations of a request run for the caller :attr:`callers` tells, by
    :meth:`run_operation`; the exceptions answer by the policies of
    :attr:`errors`.
    """

    project: "StarletteProject"

    callers = Slot(StarletteCallers)
    errors = Slot(StarletteErrorsUnit)

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

    def _iter_middleware(self) -> "Iterator[Middleware]":
        """
        The middleware, the outermost first: none here. A subclass adding to
        those of its base yields them too.
        """
        return iter(())
