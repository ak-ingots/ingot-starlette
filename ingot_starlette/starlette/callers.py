"""The callers: who a request or a WebSocket is of."""

__all__ = ("StarletteCallers",)

import typing as t

from ingots.puer import Entity

if t.TYPE_CHECKING:
    from ingots.defaults import Project
    from ingots.defaults.operations import Caller
    from starlette.requests import HTTPConnection


class StarletteCallers(Entity):
    """
    Tells the caller of a request or a WebSocket by what it bears, its
    headers, its cookies, its session: the anonymous one of
    ``operations.callers`` here. An addon telling the callers by a session,
    a token, overrides :meth:`_get_caller`.
    """

    project: "Project"

    @t.final
    async def get(self, connection: "HTTPConnection") -> "Caller":
        """The caller of a request or a WebSocket."""
        return await self._get_caller(connection)

    async def _get_caller(self, connection: "HTTPConnection") -> "Caller":
        return self.project.operations.callers.get_anonymous()
