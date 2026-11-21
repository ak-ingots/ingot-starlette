"""
The echo of a WebSocket: ``{"text": ...}`` echoed for each message, by the
operation of its caller; ``{"text": "fail"}`` fails, its problem closing
the WebSocket by 4409.
"""

__all__ = ("StreamResource",)

import typing as t

from ingot_starlette.starlette.websockets import BaseStarletteWebSocketResource

if t.TYPE_CHECKING:
    from ingots.puer import BoundFactory

    from demo.echo.operations import BaseEchoOperation
    from demo.project import EchoProject


class StreamResource(BaseStarletteWebSocketResource):
    project: "EchoProject"

    @t.override
    async def _receive(self, message: t.Any) -> None:
        text = message["text"]
        echo = self.project.echo
        factory: "BoundFactory[BaseEchoOperation]" = (
            echo.op_fail if text == "fail" else echo.op_send
        )
        await self.send({"text": await self.run_operation(factory, text)})
