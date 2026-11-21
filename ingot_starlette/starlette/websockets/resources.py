"""The resources of the WebSockets: an entity for each connection, its state."""

__all__ = ("BaseStarletteWebSocketResource", "StarletteWebSocketRoute")

import abc
import asyncio
import json
import typing as t

from ingots.puer import Entity
from starlette.exceptions import HTTPException
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket, WebSocketState

from ..errors import encode_problem

if t.TYPE_CHECKING:
    from ingots.defaults.operations import BaseOperation, Caller
    from ingots.puer import BoundFactory

    from ingot_starlette.project import StarletteProject

_GOING_AWAY: t.Final = 1001


class BaseStarletteWebSocketResource(Entity):
    """
    A WebSocket, a resource of a state of its own: an entity for each
    connection, created by a :class:`~ingots.puer.Factory` of its subtree,
    gone with it; what it keeps lives in its attributes::

        class ChatResource(BaseStarletteWebSocketResource):
            @t.override
            async def _open(self) -> None:
                self._room = self.websocket.path_params["room"]

            @t.override
            async def _receive(self, message: t.Any) -> None:
                echo = await self.run_operation(op_send, message["text"])
                await self.send({"echo": echo})

    Its caller is told once, at the handshake, and each of its operations
    runs for it, :meth:`run_operation`. :meth:`_open` may refuse it, raising,
    before it is accepted; each message, of JSON, goes to :meth:`_receive`; a
    failure of either closes it by its problem, ``4000 + status``, and
    :meth:`send_problem` tells one without closing. A shutdown closes it as
    going away, 1001, for the client to come back; :meth:`_close` runs at
    every end.
    """

    project: "StarletteProject"

    _websocket: WebSocket
    _caller: "Caller"

    @t.final
    @property
    def websocket(self) -> WebSocket:
        """The WebSocket of Starlette, once served."""
        return self._websocket

    @t.final
    @property
    def caller(self) -> "Caller":
        """The caller of the connection, told at the handshake."""
        return self._caller

    @t.final
    async def serve(self, websocket: WebSocket) -> None:
        """Opens the WebSocket, its caller told, then reads it to its end."""
        self._websocket = websocket
        self._caller = await self.project.starlette.callers.get(websocket)
        try:
            await self._open()
            await websocket.accept(subprotocol=self._get_subprotocol())
            async for text in websocket.iter_text():
                try:
                    message = json.loads(text)
                except ValueError:
                    raise HTTPException(400, "a message is not JSON") from None
                await self._receive(message)
        except asyncio.CancelledError:
            if websocket.application_state == WebSocketState.CONNECTED:
                await asyncio.shield(websocket.close(_GOING_AWAY))
            raise
        finally:
            await self._close()

    @t.final
    async def send(self, message: object) -> None:
        """Sends a message, of JSON."""
        await self._websocket.send_text(json.dumps(message))

    @t.final
    async def send_problem(self, error: Exception) -> None:
        """
        Sends the problem of an exception, ``{"problem": ...}``, by its
        policy, logged, the WebSocket kept: a message failed, not the
        connection.
        """
        problem = self.project.starlette.errors.encode(error, self._websocket)
        await self.send({"problem": encode_problem(problem)})

    @t.final
    async def run_operation[ParametersType, ResultType](
        self,
        factory: "BoundFactory[BaseOperation[ParametersType, ResultType]]",
        parameters: ParametersType,
    ) -> ResultType:
        """Runs an operation for the caller of the connection, a run of its own."""
        operations = self.project.operations
        metadata = operations.create_metadata(self._caller)
        return await operations.runner.run(factory, parameters, metadata)

    async def _open(self) -> None:
        """Before the accept: raising refuses the WebSocket. Nothing here."""

    @abc.abstractmethod
    async def _receive(self, message: t.Any) -> None:
        """A message, of JSON decoded."""
        raise NotImplementedError

    async def _close(self) -> None:
        """At the end, whatever it is: what the resource holds let go. Nothing here."""

    def _get_subprotocol(self) -> str | None:
        """The subprotocol of the accept, of ``Sec-WebSocket-Protocol``: none."""
        return None


class StarletteWebSocketRoute(WebSocketRoute):
    """
    A route of a WebSocket to a resource, a new one of its factory for each
    connection: ``StarletteWebSocketRoute("/chat/{room}", self.chat)``.
    """

    def __init__(
        self,
        path: str,
        factory: "BoundFactory[BaseStarletteWebSocketResource]",
        *,
        name: str | None = None,
    ) -> None:
        async def serve(websocket: WebSocket) -> None:
            await factory().serve(websocket)

        super().__init__(path, serve, name=name or factory.cls.__name__)
