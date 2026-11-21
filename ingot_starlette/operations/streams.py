"""
The operations giving a stream, run by the runner of today: an operation
whose result is the stream. A draft for ``ingots.defaults.operations``,
kept in the addon till it moves there.
"""

__all__ = ("BaseStreamOperation", "OperationStream")

import abc
import logging
import typing as t

from ingots.defaults.operations import BaseOperation
from ingots.defaults.operations.runner import CALLER_UID, RUN_UID

if t.TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from types import TracebackType

    from ingots.defaults.operations import OperationMetadata

logger = logging.getLogger(__name__)


class BaseStreamOperation[ParametersType, ItemType](
    BaseOperation[ParametersType, "OperationStream[ItemType]"]
):
    """
    An operation giving the items of a stream, its :meth:`_stream` an async
    generator: the runner checks the caller and gives the stream, not
    started, which runs as it is read, in the context of the logs of its
    run, and is closed by the reader, by ``async with``, when it is done or
    its connection is gone::

        stream = await runner.run(project.game.op_watch, game_uid, metadata)
        async with stream:
            async for state in stream:
                await websocket.send_json(state)
    """

    @t.final
    @t.override
    async def _run(
        self, parameters: ParametersType, metadata: "OperationMetadata"
    ) -> "OperationStream[ItemType]":
        return OperationStream(self, self._stream(parameters, metadata), metadata)

    @abc.abstractmethod
    def _stream(
        self, parameters: ParametersType, metadata: "OperationMetadata"
    ) -> "AsyncGenerator[ItemType]":
        """The items, an async generator; its ``finally`` runs at the close."""
        raise NotImplementedError


class OperationStream[ItemType]:
    """
    The stream of a run of a :class:`BaseStreamOperation`: each item read in
    the context of the logs of the run, a failure logged as the runner logs
    one, the close closing the generator.
    """

    def __init__(
        self,
        operation: BaseOperation[t.Any, t.Any],
        items: "AsyncGenerator[ItemType]",
        metadata: "OperationMetadata",
    ) -> None:
        self._operation = operation
        self._items = items
        self._metadata = metadata
        self._count = 0

    def __aiter__(self) -> t.Self:
        return self

    async def __anext__(self) -> ItemType:
        with (
            RUN_UID.bind(self._metadata.run_uid),
            CALLER_UID.bind(self._metadata.caller.uid),
        ):
            try:
                item = await anext(self._items)
            except StopAsyncIteration:
                logger.debug("%r: done: %s items", self._operation, self._count)
                raise
            except Exception as error:
                logger.info("%r: failed: %r", self._operation, error)
                raise
        self._count += 1
        return item

    async def __aenter__(self) -> t.Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: "TracebackType | None",
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Closes the stream: the ``finally`` of its generator runs."""
        with (
            RUN_UID.bind(self._metadata.run_uid),
            CALLER_UID.bind(self._metadata.caller.uid),
        ):
            await self._items.aclose()
