"""
The endpoint of the echo, unary: a request, a response. The paths of the
resource next to its methods; the request decoded and the response encoded
here, the work done by the operations.
"""

__all__ = ("EchoEndpoint",)

import typing as t

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from ingot_starlette.starlette import StarletteEndpoint

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from starlette.routing import BaseRoute

    from demo.project import EchoProject


class EchoEndpoint(StarletteEndpoint):
    """
    ``POST /echo {"text": ...}`` and ``GET /echo/{text}``, ``{"text": ...}``;
    ``POST /fail {"text": ...}``, 409, the problem of its policy.
    """

    project: "EchoProject"

    async def send(self, request: Request) -> Response:
        text = (await request.json())["text"]
        return JSONResponse({"text": await self._run_send(text, request)})

    async def send_path(self, request: Request) -> Response:
        text = request.path_params["text"]
        return JSONResponse({"text": await self._run_send(text, request)})

    async def fail(self, request: Request) -> Response:
        text = (await request.json())["text"]
        starlette, echo = self.project.starlette, self.project.echo
        await starlette.run_operation(echo.op_fail, text, request)
        return Response(status_code=204)  # never: the operation fails

    @t.override
    def _iter_routes(self) -> "Iterator[BaseRoute]":
        yield Route("/echo", self.send, methods=["POST"])
        yield Route("/echo/{text}", self.send_path)
        yield Route("/fail", self.fail, methods=["POST"])

    async def _run_send(self, text: str, request: Request) -> str:
        starlette, echo = self.project.starlette, self.project.echo
        return await starlette.run_operation(echo.op_send, text, request)
