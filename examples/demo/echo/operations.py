"""The operations of the echo: what a transport runs, of none of its own."""

__all__ = (
    "BaseEchoOperation",
    "FailEchoOperation",
    "SendEchoOperation",
    "TicksOperation",
    "TicksParameters",
)

import asyncio
import logging
import typing as t
from dataclasses import dataclass

from ingots.defaults.operations import BaseOperation, OperationMetadata, Permissions

from ingot_starlette.operations import BaseStreamOperation

from .errors import EchoFailedError

if t.TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from . import EchoUnit

logger = logging.getLogger(__name__)


class BaseEchoOperation(BaseOperation[str, str]):
    """An operation of the echo, anyone may run."""

    parent: "EchoUnit"

    @t.override
    def _get_permissions(self) -> Permissions:
        permissions = self.parent.permissions
        return permissions(permissions.flags.CAN_ECHO)


class SendEchoOperation(BaseEchoOperation):
    @t.override
    async def _run(self, parameters: str, metadata: OperationMetadata) -> str:
        return parameters


class FailEchoOperation(BaseEchoOperation):
    @t.override
    async def _run(self, parameters: str, metadata: OperationMetadata) -> str:
        raise EchoFailedError.for_text(parameters)


@dataclass(frozen=True, slots=True, kw_only=True)
class TicksParameters:
    """``count`` ticks, 0 no end, ``interval`` seconds apart, failing at ``fail_at``."""

    count: int = 0
    interval: float = 0.1
    fail_at: int = 0


class TicksOperation(BaseStreamOperation[TicksParameters, int]):
    """The ticks, a stream: what a server sends of itself, a state of a game."""

    parent: "EchoUnit"

    @t.override
    def _get_permissions(self) -> Permissions:
        permissions = self.parent.permissions
        return permissions(permissions.flags.CAN_ECHO)

    @t.override
    async def _stream(
        self, parameters: TicksParameters, metadata: OperationMetadata
    ) -> "AsyncGenerator[int]":
        tick = 0
        try:
            while not parameters.count or tick < parameters.count:
                tick += 1
                if tick == parameters.fail_at:
                    raise EchoFailedError.for_text(f"tick {tick}")
                yield tick
                await asyncio.sleep(parameters.interval)
        finally:
            logger.info("%r: closed at %s", self, tick)
