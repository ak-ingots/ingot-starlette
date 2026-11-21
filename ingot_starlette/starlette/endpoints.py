"""The endpoints: the entities whose methods the routes of Starlette call."""

__all__ = ("StarletteEndpoint",)

import typing as t

from ingots.puer import Entity

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from starlette.routing import BaseRoute

    from ingots.defaults import Project


class StarletteEndpoint(Entity):
    """
    The endpoint of a resource, as a servicer of gRPC is of a service: its
    methods take a request of Starlette, or a WebSocket, and give its
    response, as Starlette's own, the operations run by
    ``project.starlette.run_operation``; :meth:`_iter_routes` routes to them,
    the paths of the resource beside its methods::

        class EchoEndpoint(StarletteEndpoint):
            @t.override
            def _iter_routes(self):
                yield Route("/echo", self.send, methods=["POST"])

            async def send(self, request: Request) -> Response:
                text = (await request.json())["text"]
                starlette = self.project.starlette
                echo = await starlette.run_operation(op_send, text, request)
                return JSONResponse({"text": echo})

    Its project is any: an endpoint of an addon, its RPCs mixed in, takes the
    project of the addon. The routes make a tree: an endpoint that is a unit
    too holds endpoints in its slots and mounts their routes under its paths,
    the Starlette unit the root. A subclass adds routes to those of its base,
    ``yield from super()._iter_routes()``.
    """

    # any project: a mixin of an addon narrows it to its own, the run of the
    # operations, ``project.starlette``, is of the Starlette unit
    project: "Project"

    @t.final
    def get_routes(self) -> "list[BaseRoute]":
        """The routes to the methods of the endpoint, and of those it mounts."""
        return list(self._iter_routes())

    def _iter_routes(self) -> "Iterator[BaseRoute]":
        """The routes: none here."""
        return iter(())
