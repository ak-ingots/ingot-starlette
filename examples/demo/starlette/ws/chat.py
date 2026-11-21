"""
A WebSocket of both, its state its own: ``{"op": "echo", "text": ...}`` a
unary operation, answered ``{"echo": ...}``; ``{"op": "ticks", ...}`` a
stream sent beside, ``{"tick": n}``, till ``{"op": "stop"}`` or the end; a
failure of either a message ``{"problem": ...}``, the WebSocket kept.
"""

__all__ = ("ChatResource",)

import asyncio
import typing as t

from ingot_starlette.starlette.websockets import BaseStarletteWebSocketResource

from demo.echo.operations import TicksParameters

if t.TYPE_CHECKING:
    from demo.project import EchoProject


class ChatResource(BaseStarletteWebSocketResource):
    project: "EchoProject"

    _ticks: "asyncio.Task[None] | None" = None

    @t.override
    async def _receive(self, message: t.Any) -> None:
        match message["op"]:
            case "echo":
                try:
                    echo = await self.run_operation(
                        self.project.echo.op_send, message["text"]
                    )
                except Exception as error:
                    await self.send_problem(error)
                    return
                await self.send({"echo": echo})
            case "ticks":
                await self._stop_ticks()
                parameters = TicksParameters(
                    count=message.get("count", 0),
                    interval=message.get("interval", 0.1),
                    fail_at=message.get("fail_at", 0),
                )
                self._ticks = asyncio.create_task(self._send_ticks(parameters))
            case "stop":
                await self._stop_ticks()

    @t.override
    async def _close(self) -> None:
        await self._stop_ticks()

    async def _send_ticks(self, parameters: TicksParameters) -> None:
        try:
            stream = await self.run_operation(self.project.echo.op_ticks, parameters)
            async with stream:
                async for tick in stream:
                    await self.send({"tick": tick})
        except Exception as error:
            await self.send_problem(error)

    async def _stop_ticks(self) -> None:
        if self._ticks is not None:
            self._ticks.cancel()
            await asyncio.gather(self._ticks, return_exceptions=True)
            self._ticks = None
