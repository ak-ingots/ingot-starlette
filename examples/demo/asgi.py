"""
The application of Starlette, the project inside: ``uvicorn asgi:app``, from its
root.
Beside the project, what is written the Starlette way, of no slot: here a
function and a router, as an application keeps its static files, or mounts
an application not yet moved into the project.
"""

from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route, Router

from ingot_starlette.runner import StarletteRunner

from project import EchoProject


async def version(request: Request) -> Response:
    """A function endpoint: the project by its application."""
    return PlainTextResponse(f"{type(request.app.project).__name__} 1.0")


async def health(request: Request) -> Response:
    return PlainTextResponse("ok")


app = StarletteRunner(EchoProject)
app.add_route("/version", version)
app.mount("/health", Router([Route("/", health)]))
