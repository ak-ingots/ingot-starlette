"""
The home page, of a browser without a script: a form of the echo posted,
the echo by a redirect, Post/Redirect/Get, so that a reload posts nothing
again; a failure a page of HTML, its policy's, the renderer of the pages.
"""

__all__ = ("HomePage",)

import html
import typing as t
import urllib.parse

from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.routing import Route

from ingot_starlette.starlette import StarletteEndpoint

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from starlette.routing import BaseRoute

    from project import EchoProject


class HomePage(StarletteEndpoint):
    """``GET /`` the form; ``POST /echo`` and ``POST /fail`` of the form."""

    project: "EchoProject"

    async def show(self, request: Request) -> Response:
        echo = request.query_params.get("echo")
        said = f"<p>The echo: <output>{html.escape(echo)}</output></p>" if echo else ""
        return HTMLResponse(
            "<!doctype html><html><head><title>Echo</title></head><body>"
            f"<h1>Echo</h1>{said}"
            '<form method="post" action="/echo"><input name="text">'
            '<button>Echo</button><button formaction="/fail">Fail</button>'
            '</form><p><a href="/socket">the echo over a WebSocket</a></p>'
            "</body></html>"
        )

    async def send(self, request: Request) -> Response:
        text = await self._read_text(request)
        starlette, echo = self.project.starlette, self.project.echo
        said = await starlette.run_operation(echo.op_send, text, request)
        query = urllib.parse.urlencode({"echo": said})
        return RedirectResponse(f"/?{query}", status_code=303)

    async def fail(self, request: Request) -> Response:
        text = await self._read_text(request)
        starlette, echo = self.project.starlette, self.project.echo
        await starlette.run_operation(echo.op_fail, text, request)
        return RedirectResponse("/", status_code=303)  # never: the operation fails

    @t.override
    def _iter_routes(self) -> "Iterator[BaseRoute]":
        yield Route("/", self.show, name="home")
        yield Route("/echo", self.send, methods=["POST"])
        yield Route("/fail", self.fail, methods=["POST"])

    async def _read_text(self, request: Request) -> str:
        # a form of a field, urlencoded: no python-multipart for so little
        form = urllib.parse.parse_qs((await request.body()).decode())
        return form.get("text", [""])[0]
