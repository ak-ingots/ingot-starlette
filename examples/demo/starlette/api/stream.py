"""
The endpoint of a WebSocket: a text echoed for each, by the operation of its
caller; a failure goes on to the policy, which sends its problem and closes
the WebSocket by ``4000 + status``.
"""

__all__ = ("StreamEndpoint",)

import typing as t

from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket

from ingot_starlette.starlette import StarletteEndpoint

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from ingots.puer import BoundFactory
    from starlette.routing import BaseRoute

    from demo.echo.operations import BaseEchoOperation
    from demo.project import EchoProject


class StreamEndpoint(StarletteEndpoint):
    """``WS /stream``: each text echoed; ``fail`` fails, closing it by 4409."""

    project: "EchoProject"

    async def serve(self, websocket: WebSocket) -> None:
        await websocket.accept()
        echo = self.project.echo
        async for text in websocket.iter_text():
            factory: "BoundFactory[BaseEchoOperation]" = (
                echo.op_fail if text == "fail" else echo.op_send
            )
            await websocket.send_text(
                await self.project.starlette.run_operation(factory, text, websocket)
            )

    @t.override
    def _iter_routes(self) -> "Iterator[BaseRoute]":
        yield WebSocketRoute("/stream", self.serve)
